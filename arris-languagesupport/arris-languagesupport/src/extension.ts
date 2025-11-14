import * as path from 'path';
import * as vscode from 'vscode';
import { LanguageClient, LanguageClientOptions, ServerOptions } from 'vscode-languageclient/node';

export function activate(context: vscode.ExtensionContext) {
    const serverScript = path.join(context.extensionPath, 'server.py');

    const serverOptions: ServerOptions = {
        command: 'python3',
        args: [serverScript],
        options: {
            cwd: context.extensionPath,
        }
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'arris' }],
        outputChannelName: 'Arris LS',
        revealOutputChannelOn: 4,
    };

    const client = new LanguageClient(
        'arrisLanguageServer',
        'Arris Language Server',
        serverOptions,
        clientOptions
    );

    context.subscriptions.push(client);
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    return undefined;
}
