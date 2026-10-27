import 'dart:convert';
import 'package:http/http.dart' as http;

class EmailConfirmationService {
  EmailConfirmationService({required this.baseUrl});

  final String baseUrl;

  Future<Map<String, dynamic>> sendVisitEmail({
    required String beneficiaryName,
    required String beneficiaryEmail,
    required String workerName,
    String message = 'Please confirm your upcoming visit.',
    String? proposedVisitDate,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/email-visits/send'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'beneficiary_name': beneficiaryName,
        'beneficiary_email': beneficiaryEmail,
        'worker_name': workerName,
        'message': message,
        if (proposedVisitDate != null && proposedVisitDate.isNotEmpty)
          'proposed_visit_date': proposedVisitDate,
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception(body['detail'] ?? 'Unable to send visit email');
    }
    return body;
  }

  Future<Map<String, dynamic>> respond({
    required String token,
    required String answer,
    String? nextVisitDate,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/email-visits/$token/respond'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'answer': answer,
        if (nextVisitDate != null && nextVisitDate.isNotEmpty)
          'next_visit_date': nextVisitDate,
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception(body['detail'] ?? 'Unable to save response');
    }
    return body;
  }
}
