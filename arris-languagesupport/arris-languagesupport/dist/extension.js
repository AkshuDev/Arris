"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const path = require("path");
const node_1 = require("vscode-languageclient/node");
function activate(context) {
    const serverScript = path.join(context.extensionPath, 'server.py');
    const serverOptions = {
        command: 'python3',
        args: [serverScript],
        options: {
            cwd: context.extensionPath,
        }
    };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'arris' }],
        outputChannelName: 'Arris LS',
        revealOutputChannelOn: 4,
    };
    const client = new node_1.LanguageClient('arrisLanguageServer', 'Arris Language Server', serverOptions, clientOptions);
    context.subscriptions.push(client);
    client.start();
}
function deactivate() {
    return undefined;
}
//# sourceMappingURL=extension.js.map