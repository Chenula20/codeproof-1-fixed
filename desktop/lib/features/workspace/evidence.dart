import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app/theme.dart';
import '../../domain/workspace_controller.dart';
import '../../ui/glass.dart';

class EvidencePanel extends StatelessWidget {
  const EvidencePanel({
    super.key,
    required this.controller,
    required this.expanded,
    required this.onToggle,
    required this.onValidate,
  });
  final WorkspaceController controller;
  final bool expanded;
  final VoidCallback onToggle;
  final VoidCallback onValidate;
  @override
  Widget build(BuildContext context) {
    final data = controller.data!;
    return GlassPanel(
      blur: true,
      padding: EdgeInsets.zero,
      radius: 16,
      child: Column(
        children: [
          SizedBox(
            height: 45,
            child: Row(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        for (final (tab, label, icon) in const [
                          (
                            EvidenceTab.problems,
                            'Problems',
                            Icons.error_outline,
                          ),
                          (EvidenceTab.tests, 'Tests', Icons.checklist_rounded),
                          (
                            EvidenceTab.sandbox,
                            'Sandbox',
                            Icons.terminal_rounded,
                          ),
                          (
                            EvidenceTab.readiness,
                            'Readiness',
                            Icons.verified_outlined,
                          ),
                          (
                            EvidenceTab.activity,
                            'Activity',
                            Icons.history_rounded,
                          ),
                        ])
                          TextButton.icon(
                            onPressed: () {
                              controller.selectEvidence(tab);
                              if (!expanded) onToggle();
                            },
                            icon: Icon(icon, size: 14),
                            label: Text(label),
                            style: TextButton.styleFrom(
                              foregroundColor: controller.evidence == tab
                                  ? Palette.cyan
                                  : Palette.muted,
                              textStyle: const TextStyle(
                                fontFamily: 'Segoe UI',
                                fontSize: 11,
                              ),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                if (MediaQuery.sizeOf(context).width > 650)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: StatusBadge(
                      data.practice ? 'PRACTICE EVIDENCE' : 'DOCKER EVIDENCE',
                      color: Palette.violet,
                    ),
                  ),
                IconButton(
                  tooltip: expanded
                      ? 'Collapse evidence panel'
                      : 'Expand evidence panel',
                  onPressed: onToggle,
                  icon: Icon(
                    expanded
                        ? Icons.keyboard_arrow_down
                        : Icons.keyboard_arrow_up,
                    size: 19,
                  ),
                ),
              ],
            ),
          ),
          if (expanded)
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 10, 22, 18),
                child: Align(
                  alignment: Alignment.topLeft,
                  child: switch (controller.evidence) {
                    EvidenceTab.problems => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          data.hasChallenge
                              ? 'Challenge observations'
                              : 'Review focus',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 7),
                        Text(
                          data.hasChallenge
                              ? data.sample
                                    ? 'POST /api/login → HTTP 422 · Missing credentials\nTrace the request contract in the challenge copy.'
                                    : data.challengeDescription
                              : data.issues.join('\n'),
                          style: const TextStyle(
                            color: Palette.muted,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    EvidenceTab.tests => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              data.validation.status == 'passed'
                                  ? Icons.check_circle_outline
                                  : Icons.info_outline,
                              color: data.validation.status == 'passed'
                                  ? Palette.mint
                                  : Palette.amber,
                              size: 18,
                            ),
                            const SizedBox(width: 9),
                            Expanded(
                              child: Text(
                                data.validation.status == 'not_run'
                                    ? 'No test evidence yet'
                                    : '${data.practice ? 'Practice' : 'Docker'} validation: ${data.validation.status}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            if (data.validation.durationMs > 0)
                              Text(
                                '${data.validation.durationMs} ms',
                                style: const TextStyle(
                                  color: Palette.muted,
                                  fontSize: 11,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        SelectableText(
                          data.validation.output,
                          style: const TextStyle(
                            fontFamily: 'Consolas',
                            color: Palette.muted,
                            fontSize: 11,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 12,
                          runSpacing: 8,
                          children: [
                            OutlinedButton(
                              onPressed: controller.busy ? null : onValidate,
                              child: Text(
                                data.practice
                                    ? 'Run practice check'
                                    : 'Run tests in Docker',
                              ),
                            ),
                            TextButton(
                              onPressed: () => controller.selectEvidence(
                                EvidenceTab.readiness,
                              ),
                              child: const Text('View release readiness →'),
                            ),
                          ],
                        ),
                      ],
                    ),
                    EvidenceTab.sandbox => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          controller.busy &&
                                  controller.operation.contains('Validating')
                              ? 'Validation in progress…'
                              : data.practice
                              ? 'In-memory practice workspace'
                              : 'Isolated Docker runner',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          data.practice
                              ? 'No container or host process is executed in practice mode. Connect the local service to run real tests.'
                              : 'Network off  ·  1 CPU  ·  256 MB memory  ·  64 processes  ·  60-second timeout\nRead-only project mount. Ephemeral container. No host shell commands.',
                          style: const TextStyle(
                            color: Palette.muted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 12),
                        if (!controller.busy)
                          OutlinedButton(
                            onPressed: onValidate,
                            child: Text(
                              data.practice
                                  ? 'Run practice check'
                                  : 'Choose test runner',
                            ),
                          ),
                      ],
                    ),
                    EvidenceTab.readiness => _readiness(context),
                    EvidenceTab.activity => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        for (final (index, event) in data.activity.indexed)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Text(
                              '0${index + 1}   $event',
                              style: const TextStyle(
                                color: Palette.muted,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  },
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _readiness(BuildContext context) {
    final data = controller.data!;
    final checks = [
      (data.evaluation?.passed == true, 'Cause explained'),
      (data.applied, 'Patch applied to copy'),
      (
        data.validation.status == 'passed',
        data.practice ? 'Practice check complete' : 'Runner passed',
      ),
      (
        data.practice || data.validation.originalUnchanged == true,
        data.practice ? 'No original accessed' : 'Original snapshot unchanged',
      ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          data.ready
              ? data.practice
                    ? 'PRACTICE COMPLETE'
                    : 'READY FOR HUMAN REVIEW'
              : 'MORE EVIDENCE NEEDED',
          style: TextStyle(
            color: data.ready ? Palette.mint : Palette.amber,
            fontSize: 19,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 13),
        Wrap(
          spacing: 24,
          runSpacing: 10,
          children: [
            for (final (passed, label) in checks)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    passed ? Icons.check_rounded : Icons.radio_button_unchecked,
                    size: 16,
                    color: passed ? Palette.mint : Palette.muted,
                  ),
                  const SizedBox(width: 7),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 11,
                      color: passed ? Palette.mint : Palette.muted,
                    ),
                  ),
                ],
              ),
          ],
        ),
        const SizedBox(height: 14),
        const Text(
          'Readiness is evidence for review, not a guarantee of production safety. Security auditing and deployment checks are not included.',
          style: TextStyle(color: Palette.muted, fontSize: 11),
        ),
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: () async {
            final report = const JsonEncoder.withIndent('  ').convert({
              'project': data.name,
              'mode': data.mode,
              'provider': data.provider,
              'phase': data.phase,
              'validation': data.validation.status,
              'output': data.validation.output,
              'original_unchanged': data.validation.originalUnchanged,
              'activity': data.activity,
              'notice': 'Review evidence only. Not a production certification.',
            });
            await Clipboard.setData(ClipboardData(text: report));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Evidence report copied')),
              );
            }
          },
          icon: const Icon(Icons.copy_outlined, size: 15),
          label: const Text('Copy evidence report'),
        ),
      ],
    );
  }
}
