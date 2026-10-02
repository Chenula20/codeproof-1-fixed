import 'package:flutter_test/flutter_test.dart';
import 'package:codeproof_desktop/domain/workspace_controller.dart';
import 'package:codeproof_desktop/services/practice_service.dart';
import 'package:codeproof_desktop/services/workspace_service.dart';

void main() {
  test('Practice writes never alter original fixtures and invalid transitions fail', () async {
    final service = PracticeWorkspaceService();
    final state = await service.open('');
    await expectLater(
      service.action(state.id, 'patch'),
      throwsA(isA<WorkspaceException>()),
    );
    await service.action(state.id, 'challenge');
    expect(state.files[loginPath], contains(badCredential));
    expect(sampleFiles[loginPath], contains(goodCredential));
    await expectLater(
      service.action(state.id, 'challenge'),
      throwsA(isA<WorkspaceException>()),
    );
    await service.action(state.id, 'explanation', {
      'explanation': 'email key is sent but username is expected',
    });
    await service.action(state.id, 'patch');
    expect(state.files[loginPath], contains(goodCredential));
    await service.close(state.id);
    final reopened = await service.open('');
    expect(reopened.phase, 'analyzed');
    expect(reopened.hints, isEmpty);
  });

  test(
    'Controller exposes operation failures and preserves the active workspace',
    () async {
      final controller = WorkspaceController(PracticeWorkspaceService());
      await controller.open();
      await controller.act('patch');
      expect(controller.error, isNotNull);
      expect(controller.busy, isFalse);
      expect(controller.data, isNotNull);
      controller.selectTab(WorkspaceTab.patch);
      expect(controller.tab, WorkspaceTab.analysis);
      await controller.act('challenge');
      expect(controller.error, isNull);
      expect(controller.tab, WorkspaceTab.investigation);
      await controller.close();
      expect(controller.data, isNull);
      controller.dispose();
    },
  );
}
