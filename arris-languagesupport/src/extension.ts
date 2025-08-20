import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const legend = new vscode.SemanticTokensLegend(
    ['keyword', 'string', 'number', 'function', 'comment', 'identifier'],
    []
  );

  context.subscriptions.push(
    vscode.languages.registerDocumentSemanticTokensProvider(
      { language: 'arris' },
      new ArrisSemanticTokensProvider(),
      legend
    )
  );
}

class ArrisSemanticTokensProvider implements vscode.DocumentSemanticTokensProvider {
  async provideDocumentSemanticTokens(
    document: vscode.TextDocument
  ): Promise<vscode.SemanticTokens> {
    const builder = new vscode.SemanticTokensBuilder();
    const keywordRegex = /\b(movn|movbn|movb|func|mov|clr|set|ret)\b/g;
    const incRegex = /@inc\b/g;
    const stringRegex = /"([^"\\]|\\.)*?"/g;
    const numberRegex = /\b\d+(\.\d+)?\b/g;
    const funcRegex = /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g;

    for (let line = 0; line < document.lineCount; line++) {
      const text = document.lineAt(line).text;
      if (text.length > 1000) continue;

      // Keywords like movn, mov, clr, set
      for (const match of text.matchAll(keywordRegex)) {
        builder.push(line, match.index ?? 0, match[0].length, 0); // keyword
      }

      // @inc directive
      for (const match of text.matchAll(incRegex)) {
        builder.push(line, match.index ?? 0, match[0].length, 0); // keyword
      }

      // Comments (## ...)
      const commentIndex = text.indexOf("##");
      if (commentIndex >= 0) {
        builder.push(line, commentIndex, text.length - commentIndex, 4); // comment
      }

      // Strings ("...")
      for (const match of text.matchAll(stringRegex)) {
        builder.push(line, match.index ?? 0, match[0].length, 1); // string
      }

      // Numbers
      for (const match of text.matchAll(numberRegex)) {
        builder.push(line, match.index ?? 0, match[0].length, 2); // number
      }

      // Function calls (identifier followed by "(")
      for (const match of text.matchAll(funcRegex)) {
        builder.push(line, match.index ?? 0, match[0].length, 3); // function
      }
    }

    return builder.build();
  }
}
