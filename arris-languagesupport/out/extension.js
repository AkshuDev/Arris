"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
const vscode = __importStar(require("vscode"));
function activate(context) {
    const legend = new vscode.SemanticTokensLegend(['keyword', 'string', 'number', 'function', 'comment', 'identifier'], []);
    context.subscriptions.push(vscode.languages.registerDocumentSemanticTokensProvider({ language: 'arris' }, new ArrisSemanticTokensProvider(), legend));
}
class ArrisSemanticTokensProvider {
    async provideDocumentSemanticTokens(document) {
        const builder = new vscode.SemanticTokensBuilder();
        const keywordRegex = /\b(movn|movbn|movb|func|mov|clr|set|ret)\b/g;
        const incRegex = /@inc\b/g;
        const stringRegex = /"([^"\\]|\\.)*?"/g;
        const numberRegex = /\b\d+(\.\d+)?\b/g;
        const funcRegex = /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g;
        for (let line = 0; line < document.lineCount; line++) {
            const text = document.lineAt(line).text;
            if (text.length > 1000)
                continue;
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
//# sourceMappingURL=extension.js.map