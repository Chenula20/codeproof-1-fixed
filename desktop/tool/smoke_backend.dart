import 'dart:io';
import 'package:codeproof_desktop/services/workspace_service.dart';

Future<void> main() async {
  final service = LocalWorkspaceService(token: Platform.environment['CODEPROOF_TOKEN']!,
    port: int.parse(Platform.environment['CODEPROOF_TEST_PORT']!));
  String? id;
  try {
    var state = await service.open('');
    id = state.id;
    if (!state.sample || state.files.isEmpty) throw StateError('Snapshot unavailable');
    state = await service.action(id, 'challenge');
    state = await service.action(id, 'hint');
    if (state.hints.length != 1) throw StateError('Hint contract mismatch');
    state = await service.action(id, 'explanation', {'explanation': 'The client sends email but the server expects the username field.'});
    if (!state.canReview) throw StateError('Patch was not unlocked');
    state = await service.action(id, 'patch');
    if (!state.applied) throw StateError('Patch did not apply');
    state = await service.action(id, 'validation', {'runner': 'python-unittest'});
    if (state.validation.status == 'not_run') throw StateError('Validation was not attempted');
    if (state.validation.originalUnchanged != true) throw StateError('Original integrity check failed');
    stdout.writeln('Desktop HTTP workflow passed. Docker result: ${state.validation.status}.');
  } finally {
    if (id != null) await service.close(id);
    service.dispose();
  }
}
