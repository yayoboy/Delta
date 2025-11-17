"""
Integrazione con strumenti di analisi statica del codice.

Supporta:
- Ruff (Python - linting e formatting)
- mypy (Python - type checking)
- pylint (Python - linting)
- ESLint (JavaScript/TypeScript)
- prettier (JavaScript/TypeScript - formatting)
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class LintIssue:
    """Rappresenta un problema rilevato dal linter."""
    file: str
    line: int
    column: int
    severity: str
    code: str
    message: str
    tool: str


class CodeLinter:
    """Gestisce l'esecuzione di strumenti di analisi statica."""

    def __init__(self, project_root: str):
        """
        Inizializza il linter.

        Args:
            project_root: Percorso radice del progetto
        """
        self.project_root = Path(project_root).resolve()

    async def _run_command(
        self,
        command: List[str],
        cwd: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        Esegue un comando in modo asincrono.

        Args:
            command: Comando e argomenti
            cwd: Working directory

        Returns:
            Tuple di (stdout, stderr, returncode)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or str(self.project_root)
            )

            stdout, stderr = await process.communicate()

            return (
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore'),
                process.returncode
            )

        except FileNotFoundError:
            return "", f"Comando non trovato: {command[0]}", 1

    def _is_tool_available(self, tool: str) -> bool:
        """
        Verifica se un tool è disponibile nel sistema.

        Args:
            tool: Nome del tool

        Returns:
            True se disponibile
        """
        try:
            import shutil
            return shutil.which(tool) is not None
        except Exception:
            return False

    async def run_ruff(
        self,
        target: Optional[str] = None,
        fix: bool = False
    ) -> List[LintIssue]:
        """
        Esegue Ruff per analisi Python.

        Args:
            target: File o directory specifici (opzionale)
            fix: Se True, corregge automaticamente i problemi

        Returns:
            Lista di problemi trovati
        """
        if not self._is_tool_available("ruff"):
            return []

        path = target or "."
        command = ["ruff", "check", path, "--output-format=json"]

        if fix:
            command.append("--fix")

        stdout, stderr, returncode = await self._run_command(command)

        issues = []
        if stdout:
            try:
                data = json.loads(stdout)
                for item in data:
                    issues.append(LintIssue(
                        file=item.get('filename', ''),
                        line=item.get('location', {}).get('row', 0),
                        column=item.get('location', {}).get('column', 0),
                        severity='warning',
                        code=item.get('code', ''),
                        message=item.get('message', ''),
                        tool='ruff'
                    ))
            except json.JSONDecodeError:
                pass

        return issues

    async def run_mypy(
        self,
        target: Optional[str] = None
    ) -> List[LintIssue]:
        """
        Esegue mypy per type checking Python.

        Args:
            target: File o directory specifici (opzionale)

        Returns:
            Lista di problemi trovati
        """
        if not self._is_tool_available("mypy"):
            return []

        path = target or "."
        command = ["mypy", path, "--no-color-output", "--show-column-numbers"]

        stdout, stderr, returncode = await self._run_command(command)

        issues = []
        output = stdout + stderr

        # Parse mypy output (format: file.py:line:col: severity: message)
        for line in output.split('\n'):
            if ':' in line and '.py' in line:
                parts = line.split(':', 4)
                if len(parts) >= 4:
                    try:
                        issues.append(LintIssue(
                            file=parts[0].strip(),
                            line=int(parts[1]),
                            column=int(parts[2]) if parts[2].strip().isdigit() else 0,
                            severity=parts[3].strip(),
                            code='mypy',
                            message=parts[4].strip() if len(parts) > 4 else '',
                            tool='mypy'
                        ))
                    except (ValueError, IndexError):
                        continue

        return issues

    async def run_pylint(
        self,
        target: Optional[str] = None
    ) -> List[LintIssue]:
        """
        Esegue pylint per analisi Python.

        Args:
            target: File o directory specifici (opzionale)

        Returns:
            Lista di problemi trovati
        """
        if not self._is_tool_available("pylint"):
            return []

        path = target or "."
        command = ["pylint", path, "--output-format=json"]

        stdout, stderr, returncode = await self._run_command(command)

        issues = []
        if stdout:
            try:
                data = json.loads(stdout)
                for item in data:
                    issues.append(LintIssue(
                        file=item.get('path', ''),
                        line=item.get('line', 0),
                        column=item.get('column', 0),
                        severity=item.get('type', 'warning'),
                        code=item.get('symbol', ''),
                        message=item.get('message', ''),
                        tool='pylint'
                    ))
            except json.JSONDecodeError:
                pass

        return issues

    async def run_eslint(
        self,
        target: Optional[str] = None,
        fix: bool = False
    ) -> List[LintIssue]:
        """
        Esegue ESLint per analisi JavaScript/TypeScript.

        Args:
            target: File o directory specifici (opzionale)
            fix: Se True, corregge automaticamente i problemi

        Returns:
            Lista di problemi trovati
        """
        if not self._is_tool_available("eslint"):
            return []

        path = target or "."
        command = ["eslint", path, "--format=json"]

        if fix:
            command.append("--fix")

        stdout, stderr, returncode = await self._run_command(command)

        issues = []
        if stdout:
            try:
                data = json.loads(stdout)
                for file_result in data:
                    for message in file_result.get('messages', []):
                        issues.append(LintIssue(
                            file=file_result.get('filePath', ''),
                            line=message.get('line', 0),
                            column=message.get('column', 0),
                            severity=message.get('severity', 1) == 2 and 'error' or 'warning',
                            code=message.get('ruleId', ''),
                            message=message.get('message', ''),
                            tool='eslint'
                        ))
            except json.JSONDecodeError:
                pass

        return issues

    async def run_all_python(
        self,
        target: Optional[str] = None,
        fix: bool = False
    ) -> Dict[str, List[LintIssue]]:
        """
        Esegue tutti i linter Python disponibili.

        Args:
            target: File o directory specifici (opzionale)
            fix: Se True, corregge problemi quando possibile

        Returns:
            Dizionario tool_name -> lista problemi
        """
        results = {}

        # Esegui in parallelo per performance
        tasks = []

        if self._is_tool_available("ruff"):
            tasks.append(("ruff", self.run_ruff(target, fix)))

        if self._is_tool_available("mypy"):
            tasks.append(("mypy", self.run_mypy(target)))

        if self._is_tool_available("pylint"):
            tasks.append(("pylint", self.run_pylint(target)))

        for tool_name, task in tasks:
            issues = await task
            results[tool_name] = issues

        return results

    async def run_all_javascript(
        self,
        target: Optional[str] = None,
        fix: bool = False
    ) -> Dict[str, List[LintIssue]]:
        """
        Esegue tutti i linter JavaScript/TypeScript disponibili.

        Args:
            target: File o directory specifici (opzionale)
            fix: Se True, corregge problemi quando possibile

        Returns:
            Dizionario tool_name -> lista problemi
        """
        results = {}

        if self._is_tool_available("eslint"):
            issues = await self.run_eslint(target, fix)
            results["eslint"] = issues

        return results

    def get_available_tools(self) -> List[str]:
        """
        Ottiene la lista di strumenti disponibili nel sistema.

        Returns:
            Lista di nomi di strumenti
        """
        tools = ["ruff", "mypy", "pylint", "eslint", "prettier"]
        return [t for t in tools if self._is_tool_available(t)]

    def format_issues(self, issues: List[LintIssue]) -> str:
        """
        Formatta i problemi in modo leggibile.

        Args:
            issues: Lista di problemi

        Returns:
            Testo formattato
        """
        if not issues:
            return "Nessun problema trovato! ✓"

        # Raggruppa per severità
        by_severity = {}
        for issue in issues:
            severity = issue.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        result = f"Trovati {len(issues)} problemi:\n\n"

        for severity in ['error', 'warning', 'info']:
            if severity in by_severity:
                issues_list = by_severity[severity]
                result += f"## {severity.upper()} ({len(issues_list)})\n\n"

                for issue in issues_list:
                    result += f"**{issue.file}:{issue.line}:{issue.column}**\n"
                    result += f"  [{issue.tool}] {issue.code}: {issue.message}\n\n"

        return result
