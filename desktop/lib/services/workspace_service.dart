import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../domain/workspace.dart';

abstract class WorkspaceService {
  Future<WorkspaceData> open(String path);
  Future<WorkspaceData> action(
    String id,
    String action, [
    Map<String, dynamic> body = const {},
  ]);
  Future<void> close(String id);
  void dispose() {}
}

class WorkspaceException implements Exception {
  const WorkspaceException(this.message);
  final String message;
  @override
  String toString() => message;
}

class LocalWorkspaceService extends WorkspaceService {
  LocalWorkspaceService({required this.token, this.port = 8000});
  final String token;
  final int port;
  final HttpClient _client = HttpClient()
    ..connectionTimeout = const Duration(seconds: 5);

  Future<Map<String, dynamic>> _request(
    String method,
    String path,
    Map<String, dynamic> body,
  ) async {
    try {
      // Fixed loopback destination: the pairing token is never sent to a remote host.
      final request = await _client.openUrl(
        method,
        Uri.http('127.0.0.1:$port', path),
      );
      request.followRedirects = false;
      request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
      request.headers.contentType = ContentType.json;
      if (method != 'DELETE') {
        final bytes = utf8.encode(jsonEncode(body));
        request.contentLength = bytes.length;
        request.add(bytes);
      }
      final response = await request.close().timeout(
        const Duration(seconds: 140),
      );
      final raw = await utf8.decoder
          .bind(response)
          .join()
          .timeout(const Duration(seconds: 10));
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = decoded['detail'];
        throw WorkspaceException(
          detail is String
              ? detail
              : 'The service rejected this request. Check your inputs.',
        );
      }
      return decoded;
    } on SocketException {
      throw const WorkspaceException(
        'Cannot reach the local service. Start python -m backend, then check the pairing token and port.',
      );
    } on TimeoutException {
      throw const WorkspaceException(
        'The local service timed out. Reopen the project to refresh its state before retrying.',
      );
    } on FormatException {
      throw const WorkspaceException(
        'The service returned an unreadable response. Check that the port belongs to CodeProof.',
      );
    }
  }

  @override
  Future<WorkspaceData> open(String path) async => WorkspaceData.fromJson(
    await _request('POST', '/v1/sessions', {'path': path}),
  );
  @override
  Future<WorkspaceData> action(
    String id,
    String action, [
    Map<String, dynamic> body = const {},
  ]) async => WorkspaceData.fromJson(
    await _request('POST', '/v1/sessions/$id/$action', body),
  );
  @override
  Future<void> close(String id) async {
    await _request('DELETE', '/v1/sessions/$id', {});
  }

  @override
  void dispose() => _client.close(force: true);
}
