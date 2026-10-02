import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:codeproof_desktop/app/app.dart';

Future<void> loadPreviewFonts() async {
  final file = File('C:/Windows/Fonts/segoeui.ttf');
  if (file.existsSync()) {
    final loader = FontLoader('Segoe UI')
      ..addFont(Future.value(ByteData.sublistView(file.readAsBytesSync())));
    await loader.load();
  }
  final mono = File('C:/Windows/Fonts/consola.ttf');
  if (mono.existsSync()) {
    final loader = FontLoader('Consolas')
      ..addFont(Future.value(ByteData.sublistView(mono.readAsBytesSync())));
    await loader.load();
  }
  final icons = FontLoader('MaterialIcons')
    ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
  await icons.load();
}

Future<void> capture(WidgetTester tester, String name) async {
  if (!const bool.fromEnvironment('CAPTURE_PREVIEWS')) return;
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find.byKey(const Key('preview')),
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    final file = File('build/previews/$name.png');
    file.parent.createSync(recursive: true);
    file.writeAsBytesSync(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

Future<void> boot(WidgetTester tester, Size size) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    const RepaintBoundary(key: Key('preview'), child: CodeProofApp()),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUpAll(loadPreviewFonts);
  testWidgets('Complete guided workflow, including locked steps and evidence', (
    tester,
  ) async {
    await boot(tester, const Size(1440, 960));
    expect(find.text('Build with AI.\nUnderstand the code.'), findsOneWidget);
    await capture(tester, '01-welcome');
    await tester.tap(find.text('Open sample project'));
    await tester.pumpAndSettle();
    expect(find.text('Student Event Management'), findsWidgets);
    await capture(tester, '02-analysis');
    await tester.tap(find.text('Patch Review'));
    await tester.pumpAndSettle();
    expect(find.text('Where to focus'), findsOneWidget);
    await tester.tap(find.text('Skill Map'));
    await tester.pumpAndSettle();
    expect(find.text('Engineering skill map'), findsOneWidget);
    await capture(tester, '03-skill-map');
    await tester.tap(find.text('Code'));
    await tester.pumpAndSettle();
    await capture(tester, '04-code');
    await tester.tap(find.text('Break My App').first);
    await tester.pumpAndSettle();
    await capture(tester, '05-challenge-dialog');
    await tester.tap(find.text('Start challenge'));
    await tester.pumpAndSettle();
    expect(find.text('Authentication Failure'), findsWidgets);
    await capture(tester, '06-investigation');
    await tester.tap(find.text('Get hint'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('explanation-field')));
    await tester.enterText(
      find.byKey(const Key('explanation-field')),
      'The database is probably slow.',
    );
    await tester.ensureVisible(find.text('Evaluate explanation'));
    await tester.tap(find.text('Evaluate explanation'));
    await tester.pumpAndSettle();
    expect(find.text('Keep investigating'), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('explanation-field')),
      'The client sends email but the handler expects username, a field mismatch.',
    );
    await tester.ensureVisible(find.text('Evaluate explanation'));
    await tester.tap(find.text('Evaluate explanation'));
    await tester.pumpAndSettle();
    expect(find.text('A small change.\nA clearer contract.'), findsOneWidget);
    await capture(tester, '07-patch-review');
    await tester.ensureVisible(find.text('Apply to challenge copy'));
    await tester.tap(find.text('Apply to challenge copy'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Run practice validation'));
    await tester.tap(find.text('Run practice validation'));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(find.text('Practice validation: passed'), findsOneWidget);
    await tester.tap(find.text('Readiness'));
    await tester.pumpAndSettle();
    expect(find.text('PRACTICE COMPLETE'), findsOneWidget);
    await capture(tester, '08-readiness');
    expect(tester.takeException(), isNull);
  });

  for (final size in [
    const Size(400, 800),
    const Size(900, 650),
    const Size(1280, 720),
  ]) {
    testWidgets('Responsive navigation and settings at $size', (tester) async {
      await boot(tester, size);
      await tester.ensureVisible(find.text('Open sample project'));
      await tester.tap(find.text('Open sample project'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.tap(find.text('Skill Map'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.tap(find.byTooltip('Appearance & shortcuts'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Reduce transparency'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Done'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('Connection dialog validates pairing token and port', (
    tester,
  ) async {
    await boot(tester, const Size(1000, 800));
    await tester.tap(find.text('Connect your project'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Open project'));
    await tester.pumpAndSettle();
    expect(find.textContaining('at least 32 characters'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(find.text('Open sample project'), findsOneWidget);
  });
}
