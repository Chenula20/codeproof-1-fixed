import '../domain/workspace.dart';
import 'workspace_service.dart';

const loginPath = 'src/frontend/login.js';
const goodCredential = '{ username: username, password }';
const badCredential = '{ email: username, password }';
const practiceHints = [
  'Trace the data crossing the login boundary. Does validation fail before the password is checked?',
  'Compare the browser login request with the authentication handler that receives it.',
  'The handler reads username. Inspect the key in the JSON body in login.js.',
  'The client sends email, but the handler requires username. Restore the username key, then test valid, invalid, and missing credentials.',
];

const sampleFiles = {
  'README.md': '# Student Event Management\n\nA small teaching project for understanding request contracts.\n\nExplore the client, handler, repository, and tests.\nStart a challenge to introduce a controlled credential mismatch.\n\nPractice mode uses an in-memory copy. No local files are opened.\n',
  'src/api/events.py': 'def upcoming_events(events, today):\n    return [event for event in events\n            if event["date"] >= today]\n',
  'src/auth/handler.py': 'def validate_login(data):\n    username = data.get("username")\n    password = data.get("password")\n\n    if not username or not password:\n        return {"error": "Missing credentials"}, 422\n\n    if username != "student" or password != "example-only":\n        return {"error": "Invalid credentials"}, 401\n\n    return {"user": username}, 200\n',
  'src/database/repository.py': 'class EventRepository:\n    def __init__(self):\n        self.events = []\n\n    def add(self, event):\n        self.events.append(dict(event))\n\n    def all(self):\n        return [dict(event) for event in self.events]\n',
  loginPath: "export async function login(username, password) {\n  const response = await fetch('/api/login', {\n    method: 'POST',\n    headers: { 'Content-Type': 'application/json' },\n    body: JSON.stringify({ username: username, password })\n  });\n  if (!response.ok) throw new Error('Login request failed');\n  return response.json();\n}\n",
  'tests/test_auth.py': 'import unittest\nfrom src.auth.handler import validate_login\n\nclass AuthenticationTests(unittest.TestCase):\n    def test_valid_credentials(self):\n        result = validate_login({"username": "student",\n                                 "password": "example-only"})\n        self.assertEqual(result[1], 200)\n\n    def test_missing_credentials(self):\n        self.assertEqual(validate_login({})[1], 422)\n',
};

class PracticeWorkspaceService extends WorkspaceService {
  WorkspaceData? _state;
  @override
  Future<WorkspaceData> open(String path) async {
    _state = WorkspaceData(
      id: 'practice',
      name: 'Student Event Management',
      sample: true,
      files: Map.of(sampleFiles),
      summary: 'A small event application, with a browser login client, a Python credential validator, an event repository, and regression tests. Follow a request through the code to understand how the pieces fit together.',
      technologies: [
        'Python',
        'JavaScript',
        'Request validation',
        'Unit tests',
      ],
      issues: [
        'Review the contract between the login client and authentication handler.',
        'Check how missing and invalid credentials are handled.',
        'Add regression coverage at the request boundary.',
      ],
      skills: const [
        SkillEstimate('Debugging', .90, .85, [
          'src/auth/handler.py',
          'tests/test_auth.py',
        ]),
        SkillEstimate('API', .80, .80, ['src/api/events.py']),
        SkillEstimate('Database', .75, .70, ['src/database/repository.py']),
        SkillEstimate('Authentication', .95, .90, [
          'src/auth/handler.py',
          loginPath,
        ]),
        SkillEstimate('Testing', .85, .80, ['tests/test_auth.py']),
        SkillEstimate('Error Handling', .80, .75, ['src/auth/handler.py']),
      ],
      activity: [
        'Opened bundled project in memory. No disk files were read or changed.',
      ],
    );
    return _state!;
  }

  @override
  Future<WorkspaceData> action(
    String id,
    String action, [
    Map<String, dynamic> body = const {},
  ]) async {
    final s = _state;
    if (s == null) throw const WorkspaceException('Open a project first.');
    switch (action) {
      case 'challenge':
        if (s.hasChallenge) {
          throw const WorkspaceException('A challenge is already active.');
        }
        s.files[loginPath] = s.files[loginPath]!.replaceFirst(
          goodCredential,
          badCredential,
        );
        s.challengeTitle = 'Authentication Failure';
        s.challengeDescription = 'Valid users cannot sign in. The request responds with HTTP 422 before authentication completes. Trace the request and explain the root cause.';
        s.relevantFiles = [loginPath, 'src/auth/handler.py'];
        s.phase = 'investigating';
        s.activity = [
          ...s.activity,
          'Introduced a controlled failure in the in-memory practice copy.',
        ];
      case 'hint':
        if (!s.hasChallenge || s.hints.length >= 4) {
          throw const WorkspaceException('No further hints available.');
        }
        s.hints = [...s.hints, practiceHints[s.hints.length]];
      case 'explanation':
        if (s.phase != 'investigating' && s.phase != 'review') {
          throw const WorkspaceException('Start an investigation first.');
        }
        final text = (body['explanation'] as String).trim().toLowerCase();
        if (text.length < 10) {
          throw const WorkspaceException(
            'Describe the cause in a little more detail.',
          );
        }
        final passed =
            text.contains('username') &&
            text.contains('email') &&
            [
              'expect',
              'key',
              'field',
              'mismatch',
              'instead',
              'send',
            ].any(text.contains);
        s.evaluation = Evaluation(
          passed,
          passed
              ? 'You found the request field mismatch. The client sends email while the handler expects username. Review the patch and validate the credential cases.'
              : 'Compare the field sent by the client with the field required by the handler. Explain why the mismatch fails validation.',
          passed ? .95 : .35,
        );
        s.phase = passed ? 'review' : 'investigating';
        s.patch = passed
            ? const PatchProposal(
                'Align the login request credential key with the handler contract.',
                '--- a/src/frontend/login.js\n+++ b/src/frontend/login.js\n@@ -2,6 +2,6 @@\n   const response = await fetch(\'/api/login\', {\n     method: \'POST\',\n     headers: { \'Content-Type\': \'application/json\' },\n-    body: JSON.stringify({ email: username, password })\n+    body: JSON.stringify({ username: username, password })\n   });\n   if (!response.ok) throw new Error(\'Login request failed\');\n',
                [loginPath],
                'low',
                [
                  'Validate valid, invalid, and missing credentials before adoption.',
                ],
              )
            : null;
      case 'patch':
        if (s.phase != 'review' || !s.canReview) {
          throw const WorkspaceException(
            'Explain the cause and review the patch first.',
          );
        }
        s.files[loginPath] = s.files[loginPath]!.replaceFirst(
          badCredential,
          goodCredential,
        );
        s.phase = 'applied';
        s.activity = [
          ...s.activity,
          'Patch applied to the in-memory practice copy.',
        ];
      case 'validation':
        await Future<void>.delayed(const Duration(milliseconds: 650));
        final passed = s.files[loginPath]!.contains(goodCredential);
        s.validation = ValidationResult(
          status: passed ? 'passed' : 'failed',
          output: passed
              ? '[Practice] Request contract restored.\n[Practice] Valid credentials: expected 200.\n[Practice] Invalid credentials: expected 401.\n[Practice] Missing credentials: expected 422.\n\nThese are fixture expectations. Docker and project tests were not executed.'
              : '[Practice] Credential key mismatch detected.\nExpected username; found email.\n\nNo Docker container or project test was executed.',
          checks: [
            'In-memory request contract check',
            'No original files accessed',
          ],
        );
        if (s.applied && passed) s.phase = 'validated';
        s.activity = [
          ...s.activity,
          'Practice validation ${passed ? 'completed' : 'failed'}; no code executed.',
        ];
      default:
        throw const WorkspaceException(
          'This action requires a connected local service.',
        );
    }
    return s;
  }

  @override
  Future<void> close(String id) async {
    _state = null;
  }
}
