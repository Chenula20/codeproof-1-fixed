import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app/theme.dart';
import '../../domain/workspace.dart';
import '../../domain/workspace_controller.dart';
import '../../ui/glass.dart';

class WorkspacePage extends StatelessWidget {
  const WorkspacePage({
    super.key,
    required this.controller,
    required this.onChallenge,
    required this.onAnalyze,
    required this.onValidate,
    required this.onCoach,
  });
  final WorkspaceController controller;
  final VoidCallback onChallenge;
  final VoidCallback onAnalyze;
  final VoidCallback onValidate;
  final VoidCallback onCoach;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    key: PageStorageKey(controller.tab),
    padding: const EdgeInsets.all(28),
    child: switch (controller.tab) {
      WorkspaceTab.analysis => _analysis(context),
      WorkspaceTab.skills => _skills(),
      WorkspaceTab.code => _code(),
      WorkspaceTab.investigation => _investigation(),
      WorkspaceTab.patch => _patch(),
    },
  );

  Widget _analysis(BuildContext context) {
    final data = controller.data!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        PageHeading('01 / Understand your project', data.name, data.summary),
        _workflowPulse(data),
        const SizedBox(height: 28),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: data.technologies.map((e) => StatusBadge(e)).toList(),
        ),
        const SizedBox(height: 25),
        LayoutBuilder(
          builder: (context, constraints) => Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              for (final (value, label, icon, color) in [
                (
                  '${data.files.length}',
                  'snapshot files',
                  Icons.description_outlined,
                  Palette.cyan,
                ),
                (
                  '${data.skills.length}',
                  'engineering skills',
                  Icons.hub_outlined,
                  Palette.violet,
                ),
                (
                  'Read-only',
                  'original project',
                  Icons.shield_outlined,
                  Palette.mint,
                ),
              ])
                SizedBox(
                  width: constraints.maxWidth > 420
                      ? (constraints.maxWidth - 24) / 3
                      : constraints.maxWidth,
                  child: GlassPanel(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(icon, size: 18, color: color),
                        const SizedBox(height: 17),
                        Text(
                          value,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          label,
                          style: const TextStyle(
                            color: Palette.muted,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 28),
        const SectionTitle('Where to focus'),
        GlassPanel(
          child: Column(
            children: [
              for (final (index, issue) in data.issues.indexed)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 7),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '0${index + 1}',
                        style: const TextStyle(
                          color: Palette.cyan,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          issue,
                          style: const TextStyle(color: Palette.muted),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 28),
        GlassPanel(
          tint: Palette.violet,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.auto_awesome_outlined, color: Palette.violet),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Understanding is built, not generated.',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      data.sample
                          ? 'Put your understanding to work with a controlled authentication challenge.'
                          : 'Describe an observed issue and trace it through a safe copy of your code.',
                      style: const TextStyle(color: Palette.muted),
                    ),
                    const SizedBox(height: 18),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        PrimaryButton(
                          data.hasChallenge
                              ? 'Continue investigation'
                              : data.sample
                              ? 'Break My App'
                              : 'Investigate an issue',
                          icon: Icons.bolt_rounded,
                          onPressed: controller.busy
                              ? null
                              : data.hasChallenge
                              ? () => controller.selectTab(
                                  WorkspaceTab.investigation,
                                )
                              : onChallenge,
                        ),
                        if (!data.practice && !data.hasChallenge)
                          OutlinedButton.icon(
                            onPressed: controller.busy ? null : onAnalyze,
                            icon: const Icon(Icons.auto_awesome, size: 16),
                            label: const Text('Analyze with AI'),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text(
          data.practice
              ? 'Bundled practice content · no local files or external AI accessed.'
              : 'Guardian snapshot · secrets and unsupported files are excluded.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  Widget _workflowPulse(WorkspaceData data) {
    final steps = [
      (
        'Understand',
        'Project mapped',
        true,
        Icons.hub_outlined,
        Palette.cyan,
      ),
      (
        'Investigate',
        data.hasChallenge ? 'Challenge active' : 'Ready when you are',
        data.hasChallenge,
        Icons.manage_search_rounded,
        Palette.violet,
      ),
      (
        'Review',
        data.canReview ? 'Patch available' : 'Explain the cause',
        data.canReview,
        Icons.difference_outlined,
        Palette.amber,
      ),
      (
        'Validate',
        data.ready ? 'Evidence collected' : 'Run checks last',
        data.ready,
        Icons.fact_check_outlined,
        Palette.mint,
      ),
    ];
    final completed = steps.where((step) => step.$3).length;
    final current = data.ready
        ? 'Review complete'
        : data.canReview
        ? 'Ready to validate'
        : data.hasChallenge
        ? 'Investigation in progress'
        : 'Analysis complete';

    return GlassPanel(
      tint: Palette.cyan,
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'WORKSPACE PULSE',
                      style: TextStyle(
                        color: Palette.cyan,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.7,
                      ),
                    ),
                    const SizedBox(height: 7),
                    Text(
                      current,
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              StatusBadge(
                '$completed / ${steps.length} steps',
                color: data.ready ? Palette.mint : Palette.cyan,
                icon: data.ready
                    ? Icons.verified_outlined
                    : Icons.route_outlined,
              ),
            ],
          ),
          const SizedBox(height: 19),
          LayoutBuilder(
            builder: (context, constraints) => Row(
              children: [
                for (final (index, step) in steps.indexed) ...[
                  Expanded(
                    child: _workflowStep(
                      title: step.$1,
                      detail: step.$2,
                      complete: step.$3,
                      icon: step.$4,
                      color: step.$5,
                      compact: constraints.maxWidth < 520,
                    ),
                  ),
                  if (index < steps.length - 1)
                    SizedBox(
                      width: constraints.maxWidth < 520 ? 8 : 18,
                      child: Divider(
                        color: steps[index + 1].$3
                            ? Palette.mint.withValues(alpha: .55)
                            : Palette.line,
                        thickness: 1,
                      ),
                    ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _workflowStep({
    required String title,
    required String detail,
    required bool complete,
    required IconData icon,
    required Color color,
    required bool compact,
  }) {
    final marker = Container(
      width: compact ? 30 : 34,
      height: compact ? 30 : 34,
      decoration: BoxDecoration(
        color: color.withValues(alpha: complete ? .16 : .07),
        borderRadius: BorderRadius.circular(11),
        border: Border.all(
          color: color.withValues(alpha: complete ? .35 : .16),
        ),
      ),
      child: Icon(
        complete ? Icons.check_rounded : icon,
        color: complete ? color : Palette.muted,
        size: compact ? 15 : 17,
      ),
    );
    if (compact) {
      return Column(
        children: [
          marker,
          const SizedBox(height: 6),
          Text(
            title,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: complete ? Palette.text : Palette.muted,
            ),
          ),
        ],
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        marker,
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: complete ? Palette.text : Palette.muted,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                detail,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Palette.muted, fontSize: 10),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _skills() {
    final data = controller.data!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const PageHeading(
          '02 / Find your learning path',
          'Engineering skill map',
          'Estimates from project evidence. A guide to what to explore, not a measurement of your ability.',
        ),
        LayoutBuilder(
          builder: (context, constraints) => Wrap(
            spacing: 14,
            runSpacing: 14,
            children: [
              for (final skill in data.skills)
                SizedBox(
                  width: constraints.maxWidth > 540
                      ? (constraints.maxWidth - 14) / 2
                      : constraints.maxWidth,
                  child: GlassPanel(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SectionTitle(
                          skill.category,
                          trailing: const Icon(
                            Icons.north_east_rounded,
                            color: Palette.muted,
                            size: 15,
                          ),
                        ),
                        _meter('Relevance', skill.relevance, Palette.cyan),
                        const SizedBox(height: 10),
                        _meter('Confidence', skill.confidence, Palette.violet),
                        const SizedBox(height: 17),
                        const Text(
                          'PROJECT EVIDENCE',
                          style: TextStyle(
                            fontSize: 9,
                            letterSpacing: 1.5,
                            color: Palette.muted,
                          ),
                        ),
                        const SizedBox(height: 5),
                        if (skill.evidence.isEmpty)
                          const Text(
                            'No direct evidence found',
                            style: TextStyle(
                              color: Palette.muted,
                              fontSize: 11,
                            ),
                          ),
                        for (final path in skill.evidence)
                          Tooltip(
                            message: path,
                            child: InkWell(
                              onTap: data.files.containsKey(path)
                                  ? () => controller.selectFile(path)
                                  : null,
                              borderRadius: BorderRadius.circular(6),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 6,
                                ),
                                child: Text(
                                  path,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontFamily: 'Consolas',
                                    color: Palette.cyan,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _meter(String label, double value, Color color) => Row(
    children: [
      SizedBox(
        width: 76,
        child: Text(
          label,
          style: const TextStyle(color: Palette.muted, fontSize: 11),
        ),
      ),
      Expanded(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(5),
          child: LinearProgressIndicator(
            value: value.clamp(0, 1),
            color: color,
            backgroundColor: Palette.line,
            minHeight: 5,
          ),
        ),
      ),
      SizedBox(
        width: 42,
        child: Text(
          '${(value * 100).round()}%',
          textAlign: TextAlign.right,
          style: const TextStyle(fontSize: 11),
        ),
      ),
    ],
  );

  Widget _code() {
    final data = controller.data!;
    final source =
        data.files[controller.selectedFile] ?? 'Select a file in the explorer.';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            const StatusBadge('Read-only', icon: Icons.lock_outline_rounded),
            StatusBadge(
              data.hasChallenge ? 'Challenge copy' : 'Snapshot',
              color: Palette.violet,
            ),
          ],
        ),
        const SizedBox(height: 18),
        SectionTitle(
          controller.selectedFile,
          trailing: IconButton(
            tooltip: 'Copy file contents',
            onPressed: () => Clipboard.setData(ClipboardData(text: source)),
            icon: const Icon(Icons.copy_outlined, size: 17),
          ),
        ),
        CodeBlock(
          source: source,
          highlight: data.hasChallenge ? 'email: username' : null,
        ),
        const SizedBox(height: 17),
        const Text(
          'Changes are reviewed as a patch and applied only to the isolated copy.',
          style: TextStyle(color: Palette.muted, fontSize: 11),
        ),
      ],
    );
  }

  Widget _investigation() {
    final data = controller.data!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        PageHeading(
          '03 / Follow the evidence',
          data.challengeTitle,
          data.challengeDescription,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            StatusBadge(
              data.canReview ? 'Patch unlocked' : 'Investigating',
              color: data.canReview ? Palette.mint : Palette.cyan,
            ),
            StatusBadge(
              data.sample ? 'Authentication' : 'Debugging',
              color: Palette.violet,
            ),
          ],
        ),
        const SizedBox(height: 28),
        const SectionTitle('Start with these files'),
        for (final path in data.relevantFiles)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: GlassPanel(
              padding: EdgeInsets.zero,
              child: ListTile(
                onTap: () => controller.selectFile(path),
                leading: const Icon(
                  Icons.description_outlined,
                  color: Palette.cyan,
                  size: 19,
                ),
                title: Text(
                  path,
                  style: const TextStyle(fontFamily: 'Consolas', fontSize: 12),
                ),
                trailing: const Icon(
                  Icons.arrow_forward_rounded,
                  size: 17,
                  color: Palette.cyan,
                ),
              ),
            ),
          ),
        const SizedBox(height: 20),
        const SectionTitle('Observed behavior'),
        CodeBlock(
          source: data.sample
              ? 'POST /api/login → HTTP 422\nRequest validation failed\nResponse: Missing credentials\n\nCredential values are omitted.'
              : data.challengeDescription,
          lineNumbers: false,
        ),
        const SizedBox(height: 24),
        GlassPanel(
          tint: Palette.violet,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Make your reasoning visible.',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              const Text(
                'What is failing? Which evidence explains it? How would you verify the fix?',
                style: TextStyle(color: Palette.muted),
              ),
              const SizedBox(height: 18),
              OutlinedButton.icon(
                onPressed: onCoach,
                icon: const Icon(Icons.lightbulb_outline_rounded, size: 17),
                label: const Text('Open coach & explain'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _patch() {
    final data = controller.data!;
    final patch = data.patch;
    if (patch == null) {
      return const Text('Explain the root cause to unlock a proposed patch.');
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        PageHeading(
          '04 / Make a deliberate change',
          'A small change.\nA clearer contract.',
          patch.description,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            StatusBadge(
              'Risk: ${patch.risk}',
              color: patch.risk == 'low' ? Palette.mint : Palette.amber,
            ),
            StatusBadge(
              data.applied ? 'Applied to copy' : 'Proposed patch',
              color: Palette.cyan,
            ),
          ],
        ),
        const SizedBox(height: 22),
        for (final warning in patch.warnings)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.info_outline, size: 16, color: Palette.amber),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    warning,
                    style: const TextStyle(fontSize: 12, color: Palette.muted),
                  ),
                ),
              ],
            ),
          ),
        const SizedBox(height: 14),
        CodeBlock(source: patch.diff, diff: true, lineNumbers: false),
        const SizedBox(height: 22),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            PrimaryButton(
              data.applied
                  ? 'Applied to challenge copy'
                  : 'Apply to challenge copy',
              icon: Icons.check_rounded,
              onPressed: data.applied || controller.busy
                  ? null
                  : () => controller.act('patch'),
            ),
            OutlinedButton.icon(
              onPressed: data.applied && !controller.busy ? onValidate : null,
              icon: const Icon(Icons.play_arrow_rounded, size: 18),
              label: Text(
                data.practice
                    ? 'Run practice validation'
                    : 'Run Docker validation',
              ),
            ),
            IconButton(
              tooltip: 'Copy proposed diff',
              onPressed: () =>
                  Clipboard.setData(ClipboardData(text: patch.diff)),
              icon: const Icon(Icons.copy_outlined, size: 18),
            ),
          ],
        ),
        const SizedBox(height: 15),
        const Text(
          'Your original files remain read-only. This is a proposal until you review the validation evidence.',
          style: TextStyle(color: Palette.muted, fontSize: 11),
        ),
      ],
    );
  }
}

class CodeBlock extends StatelessWidget {
  const CodeBlock({
    super.key,
    required this.source,
    this.diff = false,
    this.lineNumbers = true,
    this.highlight,
  });
  final String source;
  final bool diff;
  final bool lineNumbers;
  final String? highlight;
  @override
  Widget build(BuildContext context) {
    final lines = source.trimRight().split('\n');
    return GlassPanel(
      padding: const EdgeInsets.symmetric(vertical: 17),
      radius: 16,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final (index, line) in lines.indexed)
              Container(
                constraints: const BoxConstraints(minWidth: 260),
                decoration: BoxDecoration(
                  color: diff && line.startsWith('+') && !line.startsWith('+++')
                      ? Palette.mint.withValues(alpha: .09)
                      : diff && line.startsWith('-') && !line.startsWith('---')
                      ? Palette.red.withValues(alpha: .09)
                      : highlight != null && line.contains(highlight!)
                      ? Palette.violet.withValues(alpha: .12)
                      : null,
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: 17,
                  vertical: 3,
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (lineNumbers)
                      SizedBox(
                        width: 34,
                        child: Text(
                          '${index + 1}',
                          style: const TextStyle(
                            fontFamily: 'Consolas',
                            fontSize: 12,
                            height: 1.5,
                            color: Palette.muted,
                          ),
                        ),
                      ),
                    SelectableText.rich(
                      TextSpan(children: _spans(line)),
                      style: const TextStyle(
                        fontFamily: 'Consolas',
                        fontSize: 12,
                        height: 1.5,
                        color: Palette.text,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  List<TextSpan> _spans(String line) {
    if (diff) {
      return [
        TextSpan(
          text: line.isEmpty ? ' ' : line,
          style: TextStyle(
            color: line.startsWith('+')
                ? Palette.mint
                : line.startsWith('-')
                ? Palette.red
                : Palette.muted,
          ),
        ),
      ];
    }
    final tokens = RegExp(
      r'''("[^"]*"|'[^']*'|\b(?:def|class|return|if|not|or|for|in|import|from|export|async|await|const|throw|new)\b|\b\d+\b|#.*)''',
    );
    final spans = <TextSpan>[];
    var end = 0;
    for (final match in tokens.allMatches(line)) {
      if (match.start > end) {
        spans.add(TextSpan(text: line.substring(end, match.start)));
      }
      final text = match.group(0)!;
      spans.add(
        TextSpan(
          text: text,
          style: TextStyle(
            color: text.startsWith('#')
                ? Palette.muted
                : text.startsWith('"') || text.startsWith("'")
                ? Palette.mint
                : Palette.violet,
          ),
        ),
      );
      end = match.end;
    }
    spans.add(
      TextSpan(
        text: end < line.length
            ? line.substring(end)
            : line.isEmpty
            ? ' '
            : '',
      ),
    );
    return spans;
  }
}
