"""
Parser del codice usando tree-sitter per estrarre simboli e relazioni.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    import tree_sitter_java as tsjava
    import tree_sitter_cpp as tscpp
    import tree_sitter_c as tsc
    import tree_sitter_go as tsgo
    import tree_sitter_rust as tsrust
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Symbol:
    """Rappresenta un simbolo nel codice."""
    name: str
    kind: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parent_name: Optional[str] = None


@dataclass
class Reference:
    """Rappresenta una referenza tra simboli."""
    from_symbol: str
    to_symbol: str
    reference_type: str
    line: int


class CodeParser:
    """Parser del codice per estrarre simboli e relazioni."""

    def __init__(self):
        """Inizializza il parser con le grammatiche tree-sitter."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter non disponibile. Installa le dipendenze: "
                "pip install tree-sitter tree-sitter-python tree-sitter-javascript ..."
            )

        self.parsers = {}
        self._init_parsers()

    def _init_parsers(self):
        """Inizializza i parser per ogni linguaggio supportato."""
        languages = {
            'python': tspython.language(),
            'javascript': tsjavascript.language(),
            'typescript': tstypescript.language_typescript(),
            'tsx': tstypescript.language_tsx(),
            'java': tsjava.language(),
            'cpp': tscpp.language(),
            'c': tsc.language(),
            'go': tsgo.language(),
            'rust': tsrust.language(),
        }

        for lang_name, language in languages.items():
            parser = Parser()
            parser.set_language(language)
            self.parsers[lang_name] = parser

    def get_parser(self, language: str) -> Optional[Parser]:
        """
        Ottiene il parser per un linguaggio.

        Args:
            language: Nome del linguaggio

        Returns:
            Parser o None se non supportato
        """
        # Mappa i nomi dei linguaggi ai parser
        lang_map = {
            'Python': 'python',
            'JavaScript': 'javascript',
            'TypeScript': 'typescript',
            'Java': 'java',
            'C++': 'cpp',
            'C': 'c',
            'C/C++ Header': 'c',
            'C++ Header': 'cpp',
            'Go': 'go',
            'Rust': 'rust',
        }

        parser_name = lang_map.get(language)
        return self.parsers.get(parser_name) if parser_name else None

    def parse_file(
        self,
        content: str,
        language: str
    ) -> Tuple[List[Symbol], List[Reference]]:
        """
        Analizza un file e estrae simboli e referenze.

        Args:
            content: Contenuto del file
            language: Linguaggio del file

        Returns:
            Tuple di (simboli, referenze)
        """
        parser = self.get_parser(language)
        if not parser:
            return [], []

        # Parse del codice
        tree = parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node

        # Estrai simboli e referenze in base al linguaggio
        if language == 'Python':
            symbols = self._extract_python_symbols(root_node, content)
            references = self._extract_python_references(root_node, content)
        elif language in ['JavaScript', 'TypeScript']:
            symbols = self._extract_js_symbols(root_node, content)
            references = self._extract_js_references(root_node, content)
        elif language == 'Java':
            symbols = self._extract_java_symbols(root_node, content)
            references = []
        elif language in ['C', 'C++', 'C/C++ Header', 'C++ Header']:
            symbols = self._extract_cpp_symbols(root_node, content)
            references = []
        elif language == 'Go':
            symbols = self._extract_go_symbols(root_node, content)
            references = []
        elif language == 'Rust':
            symbols = self._extract_rust_symbols(root_node, content)
            references = []
        else:
            symbols = []
            references = []

        return symbols, references

    def _get_node_text(self, node: 'Node', source: str) -> str:
        """Estrae il testo di un nodo."""
        return source[node.start_byte:node.end_byte]

    def _get_docstring(self, node: 'Node', source: str) -> Optional[str]:
        """Estrae la docstring di un nodo."""
        if node.type == 'expression_statement':
            string_node = node.child_by_field_name('expression')
            if string_node and string_node.type == 'string':
                text = self._get_node_text(string_node, source)
                # Rimuovi virgolette
                return text.strip('\'"')
        return None

    def _extract_python_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice Python."""
        symbols = []

        def traverse(node: 'Node', parent_name: Optional[str] = None):
            # Classi
            if node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)

                    # Cerca docstring
                    docstring = None
                    body = node.child_by_field_name('body')
                    if body and body.child_count > 0:
                        first_stmt = body.children[0]
                        docstring = self._get_docstring(first_stmt, source)

                    symbols.append(Symbol(
                        name=name,
                        kind='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        docstring=docstring
                    ))

                    # Processa metodi della classe
                    if body:
                        for child in body.children:
                            traverse(child, parent_name=name)

            # Funzioni e metodi
            elif node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    # Cerca docstring
                    docstring = None
                    body = node.child_by_field_name('body')
                    if body and body.child_count > 0:
                        first_stmt = body.children[0]
                        docstring = self._get_docstring(first_stmt, source)

                    kind = 'method' if parent_name else 'function'

                    symbols.append(Symbol(
                        name=name,
                        kind=kind,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        docstring=docstring,
                        signature=signature,
                        parent_name=parent_name
                    ))

            # Continua la traversata solo se non siamo dentro una classe
            # (le classi gestiscono i loro figli internamente)
            if node.type != 'class_definition':
                for child in node.children:
                    traverse(child, parent_name)

        traverse(root)
        return symbols

    def _extract_python_references(self, root: 'Node', source: str) -> List[Reference]:
        """Estrae referenze da codice Python."""
        references = []
        current_function = None

        def traverse(node: 'Node', in_function: Optional[str] = None):
            nonlocal current_function

            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    func_name = self._get_node_text(name_node, source)
                    # Processa il body della funzione
                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            traverse(child, in_function=func_name)

            # Import
            elif node.type == 'import_statement':
                if in_function:
                    # Trova i nomi importati
                    for child in node.children:
                        if child.type == 'dotted_name':
                            imported = self._get_node_text(child, source)
                            references.append(Reference(
                                from_symbol=in_function,
                                to_symbol=imported,
                                reference_type='import',
                                line=node.start_point[0] + 1
                            ))

            # Chiamate a funzioni
            elif node.type == 'call':
                if in_function:
                    func_node = node.child_by_field_name('function')
                    if func_node:
                        called = self._get_node_text(func_node, source)
                        # Prendi solo il nome base (senza attributi)
                        called = called.split('.')[-1] if '.' in called else called
                        references.append(Reference(
                            from_symbol=in_function,
                            to_symbol=called,
                            reference_type='call',
                            line=node.start_point[0] + 1
                        ))

            else:
                for child in node.children:
                    traverse(child, in_function)

        traverse(root)
        return references

    def _extract_js_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice JavaScript/TypeScript."""
        symbols = []

        def traverse(node: 'Node', parent_name: Optional[str] = None):
            # Classi
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    symbols.append(Symbol(
                        name=name,
                        kind='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1]
                    ))

                    # Processa metodi
                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            traverse(child, parent_name=name)

            # Funzioni
            elif node.type in ['function_declaration', 'function']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    symbols.append(Symbol(
                        name=name,
                        kind='function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        signature=signature,
                        parent_name=parent_name
                    ))

            # Metodi
            elif node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    symbols.append(Symbol(
                        name=name,
                        kind='method',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        signature=signature,
                        parent_name=parent_name
                    ))

            if node.type not in ['class_declaration']:
                for child in node.children:
                    traverse(child, parent_name)

        traverse(root)
        return symbols

    def _extract_js_references(self, root: 'Node', source: str) -> List[Reference]:
        """Estrae referenze da codice JavaScript/TypeScript."""
        # Simile a Python ma con sintassi JS
        return []

    def _extract_java_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice Java."""
        symbols = []

        def traverse(node: 'Node', parent_name: Optional[str] = None):
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    symbols.append(Symbol(
                        name=name,
                        kind='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1]
                    ))

                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            traverse(child, parent_name=name)

            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    symbols.append(Symbol(
                        name=name,
                        kind='method',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        signature=signature,
                        parent_name=parent_name
                    ))

            if node.type not in ['class_declaration']:
                for child in node.children:
                    traverse(child, parent_name)

        traverse(root)
        return symbols

    def _extract_cpp_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice C/C++."""
        symbols = []

        def traverse(node: 'Node', parent_name: Optional[str] = None):
            if node.type == 'class_specifier':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    symbols.append(Symbol(
                        name=name,
                        kind='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1]
                    ))

            elif node.type == 'function_definition':
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    # Trova il nome della funzione
                    name = self._find_function_name(declarator, source)
                    if name:
                        symbols.append(Symbol(
                            name=name,
                            kind='function',
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_col=node.start_point[1],
                            end_col=node.end_point[1]
                        ))

            for child in node.children:
                traverse(child, parent_name)

        traverse(root)
        return symbols

    def _find_function_name(self, node: 'Node', source: str) -> Optional[str]:
        """Helper per trovare il nome di una funzione in C/C++."""
        if node.type == 'function_declarator':
            declarator = node.child_by_field_name('declarator')
            if declarator:
                return self._get_node_text(declarator, source)
        elif node.type == 'identifier':
            return self._get_node_text(node, source)

        for child in node.children:
            name = self._find_function_name(child, source)
            if name:
                return name

        return None

    def _extract_go_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice Go."""
        symbols = []

        def traverse(node: 'Node'):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    symbols.append(Symbol(
                        name=name,
                        kind='function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        signature=signature
                    ))

            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    symbols.append(Symbol(
                        name=name,
                        kind='method',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1]
                    ))

            for child in node.children:
                traverse(child)

        traverse(root)
        return symbols

    def _extract_rust_symbols(self, root: 'Node', source: str) -> List[Symbol]:
        """Estrae simboli da codice Rust."""
        symbols = []

        def traverse(node: 'Node'):
            if node.type == 'function_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    params = node.child_by_field_name('parameters')
                    signature = self._get_node_text(params, source) if params else '()'

                    symbols.append(Symbol(
                        name=name,
                        kind='function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        signature=signature
                    ))

            elif node.type == 'struct_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._get_node_text(name_node, source)
                    symbols.append(Symbol(
                        name=name,
                        kind='struct',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1]
                    ))

            for child in node.children:
                traverse(child)

        traverse(root)
        return symbols
