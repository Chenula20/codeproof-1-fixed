import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../domain/workspace_controller.dart';
import '../../ui/glass.dart';

class CoachPanel extends StatelessWidget {
  const CoachPanel({
    super.key,
    required this.controller,
    required this.explanation,
    this.onClose,
  });
  final WorkspaceController controller;
  final TextEditingController explanation;
  final VoidCallback? onClose;
  @override
  Widget build(BuildContext context) {
    final data = controller.data!;
    return GlassPanel(
      blur: true,
      padding: EdgeInsets.zero,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.auto_awesome_outlined,
                  color: Palette.cyan,
                  size: 19,
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Your engineering coach',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                ),
                if (onClose != null)
                  IconButton(
                    tooltip: 'Close coach',
                    onPressed: onClose,
                    icon: const Icon(Icons.close, size: 17),
                  ),
              ],
            ),
            const SizedBox(height: 15),
            StatusBadge(
              data.sample ? 'Guided practice' : data.provider,
              color: Palette.violet,
            ),
            const SizedBox(height: 24),
            Text(
              data.hasChallenge
                  ? data.challengeTitle
                  : 'Let’s understand your project.',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 17),
            ),
            const SizedBox(height: 10),
            if (!data.hasChallenge) ...[
              const Text(
                'Start with the big picture. Explore the analysis, follow a skill to its source files, then investigate a failure.',
                style: TextStyle(color: Palette.muted),
              ),
              const SizedBox(height: 23),
              GlassPanel(
                padding: const EdgeInsets.all(16),
                tint: Palette.cyan,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.tips_and_updates_outlined,
                      color: Palette.cyan,
                      size: 22,
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'A good first question',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'What does this application expect at its boundaries — and what happens when it receives something else?',
                      style: TextStyle(color: Palette.muted, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () {
                    controller.selectTab(WorkspaceTab.skills);
                    onClose?.call();
                  },
                  child: const Text('Explore skill map'),
                ),
              ),
            ] else ...[
              StatusBadge(
                data.ready
                    ? 'Ready for review'
                    : data.canReview
                    ? 'Patch unlocked'
                    : 'Investigating',
                color: data.canReview ? Palette.mint : Palette.cyan,
              ),
              const SizedBox(height: 22),
              const Divider(),
              const SizedBox(height: 18),
              SectionTitle(
                'Progressive hints',
                trailing: Text(
                  '${data.hints.length} / 4',
                  style: const TextStyle(color: Palette.muted, fontSize: 11),
                ),
              ),
              const Text(
                'A little direction, only when you need it.',
                style: TextStyle(color: Palette.muted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: data.hints.length < 4 && !controller.busy
                      ? () => controller.act('hint')
                      : null,
                  icon: const Icon(Icons.lightbulb_outline, size: 16),
                  label: Text(
                    data.hints.length < 4 ? 'Get hint' : 'All hints revealed',
                  ),
                ),
              ),
              for (final (index, hint) in data.hints.indexed)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: GlassPanel(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '0${index + 1}  ${['Direction', 'Component', 'Specific area', 'Near solution'][index]}',
                          style: const TextStyle(
                            color: Palette.cyan,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 7),
                        Text(hint, style: const TextStyle(fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 22),
              const Divider(),
              const SizedBox(height: 18),
              const SectionTitle('Explain before you fix'),
              const Text(
                'Describe the cause and the evidence that led you there.',
                style: TextStyle(color: Palette.muted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              TextField(
                key: const Key('explanation-field'),
                controller: explanation,
                minLines: 4,
                maxLines: 8,
                maxLength: 8000,
                enabled: !controller.busy && !data.applied,
                decoration: const InputDecoration(
                  hintText: 'I think the request fails because…',
                  counterText: '',
                  labelText: 'Your explanation',
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: PrimaryButton(
                  'Evaluate explanation',
                  icon: Icons.arrow_forward_rounded,
                  onPressed: !controller.busy && !data.applied
                      ? () async {
                          await controller.act('explanation', {
                            'explanation': explanation.text,
                          });
                          if (controller.data?.canReview == true) {
                            onClose?.call();
                          }
                        }
                      : null,
                ),
              ),
              if (data.evaluation != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: GlassPanel(
                    padding: const EdgeInsets.all(14),
                    tint: data.evaluation!.passed
                        ? Palette.mint
                        : Palette.amber,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          data.evaluation!.passed
                              ? 'Root cause identified'
                              : 'Keep investigating',
                          style: TextStyle(
                            color: data.evaluation!.passed
                                ? Palette.mint
                                : Palette.amber,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          data.evaluation!.feedback,
                          style: const TextStyle(fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
            const SizedBox(height: 24),
            Text(
              data.sample
                  ? 'Practice coaching uses curated hints and a keyword-based explanation check. It is not an AI assessment.'
                  : 'AI coaching uses your redacted snapshot only after you enable AI analysis.',
              style: const TextStyle(
                fontSize: 10,
                color: Palette.muted,
                height: 1.6,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
