class SkillEstimate {
  const SkillEstimate(
    this.category,
    this.relevance,
    this.confidence,
    this.evidence,
  );
  final String category;
  final double relevance;
  final double confidence;
  final List<String> evidence;
  factory SkillEstimate.fromJson(Map<String, dynamic> json) => SkillEstimate(
    json['category'] as String,
    (json['relevance'] as num).toDouble(),
    (json['confidence'] as num).toDouble(),
    List<String>.from(json['evidence'] as List),
  );
}

class Evaluation {
  const Evaluation(this.passed, this.feedback, this.score);
  final bool passed;
  final String feedback;
  final double score;
  factory Evaluation.fromJson(Map<String, dynamic> json) => Evaluation(
    json['passed'] as bool,
    json['feedback'] as String,
    (json['score'] as num).toDouble(),
  );
}

class PatchProposal {
  const PatchProposal(
    this.description,
    this.diff,
    this.files,
    this.risk,
    this.warnings,
  );
  final String description;
  final String diff;
  final List<String> files;
  final String risk;
  final List<String> warnings;
  factory PatchProposal.fromJson(Map<String, dynamic> json) => PatchProposal(
    json['description'] as String,
    json['diff'] as String,
    List<String>.from(json['affected_files'] as List),
    json['risk_level'] as String,
    List<String>.from(json['validation_warnings'] as List),
  );
}

class ValidationResult {
  const ValidationResult({
    this.status = 'not_run',
    this.output = 'No validation has run yet.',
    this.durationMs = 0,
    this.originalUnchanged,
    this.checks = const [],
  });
  final String status;
  final String output;
  final int durationMs;
  final bool? originalUnchanged;
  final List<String> checks;
  factory ValidationResult.fromJson(Map<String, dynamic> json) =>
      ValidationResult(
        status: json['status'] as String,
        output: json['output'] as String,
        durationMs: json['duration_ms'] as int,
        originalUnchanged: json['original_unchanged'] as bool?,
        checks: List<String>.from(json['checks'] as List),
      );
}

class WorkspaceData {
  WorkspaceData({
    required this.id,
    required this.name,
    required this.sample,
    required this.files,
    required this.summary,
    required this.technologies,
    required this.issues,
    required this.skills,
    this.mode = 'Practice workspace',
    this.provider = 'Practice coach',
    this.phase = 'analyzed',
    this.challengeTitle = '',
    this.challengeDescription = '',
    this.relevantFiles = const [],
    this.hints = const [],
    this.evaluation,
    this.patch,
    this.validation = const ValidationResult(),
    this.activity = const [],
  });
  final String id;
  final String name;
  final bool sample;
  Map<String, String> files;
  String summary;
  List<String> technologies;
  List<String> issues;
  List<SkillEstimate> skills;
  String mode;
  String provider;
  String phase;
  String challengeTitle;
  String challengeDescription;
  List<String> relevantFiles;
  List<String> hints;
  Evaluation? evaluation;
  PatchProposal? patch;
  ValidationResult validation;
  List<String> activity;
  bool get hasChallenge => phase != 'analyzed';
  bool get canReview => patch != null && evaluation?.passed == true;
  bool get applied => phase == 'applied' || phase == 'validated';
  bool get ready => phase == 'validated';
  bool get practice => mode == 'Practice workspace';

  factory WorkspaceData.fromJson(Map<String, dynamic> json) => WorkspaceData(
    id: json['id'] as String,
    name: json['name'] as String,
    sample: json['sample'] as bool,
    files: Map<String, String>.from(json['files'] as Map),
    summary: json['summary'] as String,
    technologies: List<String>.from(json['technologies'] as List),
    issues: List<String>.from(json['issues'] as List),
    skills: (json['skills'] as List)
        .map((e) => SkillEstimate.fromJson(e as Map<String, dynamic>))
        .toList(),
    mode: json['mode'] as String,
    provider: json['provider'] as String,
    phase: json['phase'] as String,
    challengeTitle: json['challenge_title'] as String,
    challengeDescription: json['challenge_description'] as String,
    relevantFiles: List<String>.from(json['relevant_files'] as List),
    hints: List<String>.from(json['hints'] as List),
    evaluation: json['evaluation'] == null
        ? null
        : Evaluation.fromJson(json['evaluation'] as Map<String, dynamic>),
    patch: json['patch'] == null
        ? null
        : PatchProposal.fromJson(json['patch'] as Map<String, dynamic>),
    validation: ValidationResult.fromJson(
      json['validation'] as Map<String, dynamic>,
    ),
    activity: List<String>.from(json['activity'] as List),
  );
}
