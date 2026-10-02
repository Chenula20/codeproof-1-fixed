import 'dart:ui';

import 'package:flutter/material.dart';

import '../app/theme.dart';

class GlassSettings extends InheritedWidget {
  const GlassSettings({
    super.key,
    required this.reducedTransparency,
    required this.reducedMotion,
    required super.child,
  });
  final bool reducedTransparency;
  final bool reducedMotion;
  static GlassSettings of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<GlassSettings>()!;
  @override
  bool updateShouldNotify(GlassSettings oldWidget) =>
      reducedTransparency != oldWidget.reducedTransparency ||
      reducedMotion != oldWidget.reducedMotion;
}

class AmbientBackground extends StatelessWidget {
  const AmbientBackground({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Stack(
    children: [
      Positioned.fill(
        child: DecoratedBox(
          decoration: const BoxDecoration(
            color: Palette.background,
            gradient: RadialGradient(
              center: Alignment(-.85, -.8),
              radius: 1.25,
              colors: [
                Color(0xFF153B47),
                Color(0xFF0B1725),
                Palette.background,
              ],
              stops: [0, .45, 1],
            ),
          ),
        ),
      ),
      Positioned.fill(
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: RadialGradient(
              center: const Alignment(1, .4),
              radius: .9,
              colors: [
                const Color(0xFF392859).withValues(alpha: .6),
                Colors.transparent,
              ],
            ),
          ),
        ),
      ),
      Positioned.fill(
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: RadialGradient(
              center: const Alignment(.2, 1.3),
              radius: .7,
              colors: [Palette.cyan.withValues(alpha: .07), Colors.transparent],
            ),
          ),
        ),
      ),
      child,
    ],
  );
}

class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.radius = 20,
    this.tint,
    this.blur = false,
  });
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final Color? tint;
  final bool blur;
  @override
  Widget build(BuildContext context) {
    final solid =
        GlassSettings.of(context).reducedTransparency ||
        MediaQuery.highContrastOf(context);
    Widget content = DecoratedBox(
      decoration: BoxDecoration(
        color: solid ? Palette.panel : null,
        gradient: solid
            ? null
            : LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  (tint ?? const Color(0xFF9CB5D2)).withValues(alpha: .12),
                  Palette.panel.withValues(alpha: .50),
                ],
              ),
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(
          color: solid ? Palette.line : Colors.white.withValues(alpha: .12),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .10),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Material(
        type: MaterialType.transparency,
        child: Padding(padding: padding, child: child),
      ),
    );
    if (blur && !solid) {
      content = BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: content,
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: content,
    );
  }
}

class Brand extends StatelessWidget {
  const Brand({super.key, this.compact = false});
  final bool compact;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 34,
        height: 34,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(11),
          gradient: const LinearGradient(
            colors: [Color(0xFF285D67), Color(0xFF493A6C)],
          ),
          border: Border.all(color: Palette.cyan.withValues(alpha: .35)),
        ),
        child: const Icon(Icons.code_rounded, color: Palette.cyan, size: 24),
      ),
      if (!compact) ...[
        const SizedBox(width: 10),
        const Text(
          'CodeProof',
          style: TextStyle(
            fontSize: 19,
            fontWeight: FontWeight.w700,
            letterSpacing: -.6,
          ),
        ),
      ],
    ],
  );
}

class StatusBadge extends StatelessWidget {
  const StatusBadge(
    this.label, {
    super.key,
    this.color = Palette.muted,
    this.icon,
  });
  final String label;
  final Color color;
  final IconData? icon;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: color.withValues(alpha: .10),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: color.withValues(alpha: .15)),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 5),
        ],
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: color,
            fontWeight: FontWeight.w600,
            letterSpacing: .2,
          ),
        ),
      ],
    ),
  );
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton(
    this.label, {
    super.key,
    required this.onPressed,
    this.icon = Icons.arrow_forward_rounded,
  });
  final String label;
  final VoidCallback? onPressed;
  final IconData icon;
  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      gradient: onPressed == null
          ? null
          : const LinearGradient(
              colors: [Palette.cyan, Palette.mint, Palette.violet],
            ),
      color: onPressed == null ? Palette.line : null,
      borderRadius: BorderRadius.circular(13),
      border: Border.all(color: Colors.white.withValues(alpha: .20)),
    ),
    child: FilledButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 17),
      label: Text(label),
      style: FilledButton.styleFrom(
        backgroundColor: Colors.transparent,
        shadowColor: Colors.transparent,
        disabledBackgroundColor: Colors.transparent,
        foregroundColor: Palette.background,
        disabledForegroundColor: Palette.muted,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        textStyle: const TextStyle(
          fontFamily: 'Segoe UI',
          fontSize: 13,
          fontWeight: FontWeight.w700,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13)),
      ),
    ),
  );
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.title, {super.key, this.trailing});
  final String title;
  final Widget? trailing;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: Row(
      children: [
        Expanded(
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
        ?trailing,
      ],
    ),
  );
}

class PageHeading extends StatelessWidget {
  const PageHeading(this.eyebrow, this.title, this.description, {super.key});
  final String eyebrow;
  final String title;
  final String description;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        eyebrow.toUpperCase(),
        style: const TextStyle(
          color: Palette.cyan,
          fontSize: 10,
          fontWeight: FontWeight.w700,
          letterSpacing: 2,
        ),
      ),
      const SizedBox(height: 13),
      Text(title, style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 10),
      Text(description, style: Theme.of(context).textTheme.bodyLarge),
      const SizedBox(height: 25),
    ],
  );
}
