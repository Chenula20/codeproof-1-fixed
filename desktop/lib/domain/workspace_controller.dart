import 'package:flutter/foundation.dart';

import '../services/workspace_service.dart';
import 'workspace.dart';

enum WorkspaceTab { analysis, skills, code, investigation, patch }

enum EvidenceTab { problems, tests, sandbox, readiness, activity }

class WorkspaceController extends ChangeNotifier {
  WorkspaceController(this.service);
  WorkspaceService service;
  WorkspaceData? data;
  WorkspaceTab tab = WorkspaceTab.analysis;
  EvidenceTab evidence = EvidenceTab.problems;
  String selectedFile = 'src/auth/handler.py';
  String? error;
  bool busy = false;
  String operation = '';
  bool _disposed = false;

  Future<void> _perform(String label, Future<void> Function() task) async {
    if (busy) return;
    busy = true;
    error = null;
    operation = label;
    notifyListeners();
    try {
      await task();
    } catch (e) {
      error = e is WorkspaceException ? e.message : 'The operation could not complete. Check your connection and try again.';
    } finally {
      busy = false;
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> open({String path = '', WorkspaceService? using}) =>
      _perform('Opening project', () async {
        final next = using ?? service;
        WorkspaceData opened;
        try {
          opened = await next.open(path);
        } catch (_) {
          if (using != null) next.dispose();
          rethrow;
        }
        if (data != null) await service.close(data!.id);
        if (using != null) {
          service.dispose();
          service = next;
        }
        data = opened;
        selectedFile = opened.files.containsKey(selectedFile)
            ? selectedFile
            : opened.files.keys.first;
        tab = WorkspaceTab.analysis;
        evidence = EvidenceTab.problems;
      });

  Future<void> act(String action, [Map<String, dynamic> body = const {}]) =>
      _perform(
        switch (action) {
          'validation' => 'Validating temporary copy',
          'explanation' => 'Reviewing explanation',
          'analysis' => 'Analyzing project',
          _ => 'Updating workspace',
        },
        () async {
          if (data == null) return;
          data = await service.action(data!.id, action, body);
          if (action == 'challenge') {
            tab = WorkspaceTab.investigation;
            evidence = EvidenceTab.problems;
          }
          if (action == 'explanation' && data!.canReview) {
            tab = WorkspaceTab.patch;
          }
          if (action == 'patch') evidence = EvidenceTab.sandbox;
          if (action == 'validation') evidence = EvidenceTab.tests;
        },
      );

  Future<void> close() => _perform('Closing workspace', () async {
    if (data != null) await service.close(data!.id);
    data = null;
    tab = WorkspaceTab.analysis;
  });
  void selectTab(WorkspaceTab value) {
    if (value == WorkspaceTab.investigation && data?.hasChallenge != true) {
      return;
    }
    if (value == WorkspaceTab.patch && data?.canReview != true) return;
    tab = value;
    notifyListeners();
  }

  void selectFile(String value) {
    selectedFile = value;
    tab = WorkspaceTab.code;
    notifyListeners();
  }

  void selectEvidence(EvidenceTab value) {
    evidence = value;
    notifyListeners();
  }

  void clearError() {
    error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    service.dispose();
    super.dispose();
  }
}
