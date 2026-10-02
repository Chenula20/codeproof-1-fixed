import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../ui/glass.dart';

class StartupScreen extends StatelessWidget {
  const StartupScreen({
    super.key,
    required this.onPractice,
    required this.onConnect,
    required this.busy,
  });
  final VoidCallback onPractice;
  final VoidCallback onConnect;
  final bool busy;
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) => SingleChildScrollView(
      child: ConstrainedBox(
        constraints: BoxConstraints(minHeight: constraints.maxHeight),
        child: Center(
          child: Padding(
            padding: EdgeInsets.all(constraints.maxWidth > 900 ? 64 : 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1180),
              child: constraints.maxWidth > 950
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(flex: 6, child: _hero(context, true)),
                        const SizedBox(width: 70),
                        Expanded(flex: 4, child: _journey()),
                      ],
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _hero(context, false),
                        const SizedBox(height: 40),
                        _journey(),
                      ],
                    ),
            ),
          ),
        ),
      ),
    ),
  );

  Widget _hero(BuildContext context, bool wide) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const StatusBadge(
        'YOUR CODE. YOUR UNDERSTANDING.',
        color: Palette.cyan,
        icon: Icons.auto_awesome_outlined,
      ),
      const SizedBox(height: 28),
      Text(
        'Build with AI.\nUnderstand the code.',
        style: TextStyle(
          fontSize: wide ? 48 : 37,
          height: 1.16,
          fontWeight: FontWeight.w700,
          letterSpacing: -2,
          color: Palette.text,
        ),
      ),
      const SizedBox(height: 5),
      ShaderMask(
        shaderCallback: (rect) => const LinearGradient(
          colors: [Palette.cyan, Palette.mint, Palette.violet],
        ).createShader(rect),
        child: Text(
          'Prove you can fix it.',
          style: TextStyle(
            fontSize: wide ? 48 : 37,
            height: 1.2,
            fontWeight: FontWeight.w700,
            letterSpacing: -2,
            color: Colors.white,
          ),
        ),
      ),
      const SizedBox(height: 24),
      const Text(
        'A calmer space to explore your software, investigate failures, and turn a proposed fix into evidence you can trust.',
        style: TextStyle(fontSize: 16, color: Palette.muted, height: 1.7),
      ),
      const SizedBox(height: 30),
      Wrap(
        spacing: 12,
        runSpacing: 12,
        children: [
          PrimaryButton(
            'Open sample project',
            onPressed: busy ? null : onPractice,
            icon: Icons.play_arrow_rounded,
          ),
          OutlinedButton.icon(
            onPressed: busy ? null : onConnect,
            icon: const Icon(Icons.folder_open_rounded, size: 18),
            label: const Text('Connect your project'),
          ),
        ],
      ),
      const SizedBox(height: 12),
      const Text(
        'Sample works offline  ·  No account or API key needed',
        style: TextStyle(fontSize: 11, color: Palette.muted),
      ),
      const SizedBox(height: 34),
      const GlassPanel(
        tint: Palette.mint,
        padding: EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.verified_user_outlined, color: Palette.mint, size: 21),
            SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Your original project stays yours.',
                    style: TextStyle(
                      color: Palette.mint,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 5),
                  Text(
                    'Read-only inspection. Isolated copies. Every patch reviewed before it is applied.',
                    style: TextStyle(
                      color: Palette.muted,
                      fontSize: 12,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    ],
  );

  Widget _journey() => GlassPanel(
    blur: true,
    radius: 28,
    padding: const EdgeInsets.all(28),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'FROM CURIOSITY TO CONFIDENCE',
          style: TextStyle(
            fontSize: 10,
            letterSpacing: 1.5,
            color: Palette.muted,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 25),
        for (final (index, title, description, icon) in const [
          (
            1,
            'Understand',
            'See the architecture behind your code.',
            Icons.hub_outlined,
          ),
          (
            2,
            'Investigate',
            'Follow the evidence. Find the failure.',
            Icons.manage_search_rounded,
          ),
          (
            3,
            'Explain',
            'Build understanding before seeing a fix.',
            Icons.lightbulb_outline_rounded,
          ),
          (
            4,
            'Review',
            'A clear diff. A deliberate decision.',
            Icons.difference_outlined,
          ),
          (
            5,
            'Validate',
            'Collect test results in an isolated copy.',
            Icons.fact_check_outlined,
          ),
        ])
          Padding(
            padding: const EdgeInsets.only(bottom: 25),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(13),
                    color: (index.isOdd ? Palette.cyan : Palette.violet)
                        .withValues(alpha: .09),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: .12),
                    ),
                  ),
                  child: Icon(
                    icon,
                    size: 19,
                    color: index.isOdd ? Palette.cyan : Palette.violet,
                  ),
                ),
                const SizedBox(width: 17),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        description,
                        style: const TextStyle(
                          color: Palette.muted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  '0$index',
                  style: const TextStyle(color: Palette.muted, fontSize: 10),
                ),
              ],
            ),
          ),
        const Divider(),
        const SizedBox(height: 10),
        const Text(
          'One workspace. A complete learning loop.',
          style: TextStyle(color: Palette.muted, fontSize: 11),
        ),
      ],
    ),
  );
}
