import 'package:flutter/material.dart';

abstract final class Palette {
  static const background = Color(0xFF080E1A);
  static const panel = Color(0xFF121D30);
  static const text = Color(0xFFF1F5FC);
  static const muted = Color(0xFFA0B0C8);
  static const cyan = Color(0xFF58E6ED);
  static const mint = Color(0xFF78EBC4);
  static const violet = Color(0xFFB59BFF);
  static const amber = Color(0xFFFFCA81);
  static const red = Color(0xFFFF8F9C);
  static const line = Color(0xFF2C3A50);
}

class AppTheme {
  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    fontFamily: 'Segoe UI',
    scaffoldBackgroundColor: Palette.background,
    colorScheme: const ColorScheme.dark(
      primary: Palette.cyan,
      secondary: Palette.violet,
      surface: Palette.panel,
      onSurface: Palette.text,
      error: Palette.red,
    ),
    textTheme: const TextTheme(
      bodyMedium: TextStyle(fontSize: 13, height: 1.55, color: Palette.text),
      bodySmall: TextStyle(fontSize: 11, height: 1.5, color: Palette.muted),
      bodyLarge: TextStyle(fontSize: 15, height: 1.6, color: Palette.muted),
      titleLarge: TextStyle(
        fontSize: 21,
        fontWeight: FontWeight.w600,
        letterSpacing: -.4,
      ),
      titleMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
      headlineMedium: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.w600,
        letterSpacing: -.8,
      ),
    ),
    dividerColor: Palette.line,
    tooltipTheme: const TooltipThemeData(
      waitDuration: Duration(milliseconds: 500),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0x9910192B),
      contentPadding: const EdgeInsets.all(15),
      hintStyle: const TextStyle(color: Palette.muted, fontSize: 13),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Palette.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Palette.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Palette.cyan),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: Palette.muted),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Palette.text,
        side: const BorderSide(color: Palette.line),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13)),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: Palette.panel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(26),
        side: const BorderSide(color: Palette.line),
      ),
    ),
  );
}
