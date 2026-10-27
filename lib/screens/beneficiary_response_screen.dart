import 'package:flutter/material.dart';
import 'email_confirmation_service.dart';

class BeneficiaryResponseScreen extends StatefulWidget {
  const BeneficiaryResponseScreen({
    super.key,
    required this.apiBaseUrl,
    required this.invitationToken,
  });

  final String apiBaseUrl;
  final String invitationToken;

  @override
  State<BeneficiaryResponseScreen> createState() => _BeneficiaryResponseScreenState();
}

class _BeneficiaryResponseScreenState extends State<BeneficiaryResponseScreen> {
  DateTime? _nextVisit;
  bool _saving = false;
  String? _status;

  Future<void> _chooseDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _nextVisit ?? now,
      firstDate: DateTime(now.year, now.month, now.day),
      lastDate: DateTime(now.year + 3),
    );
    if (picked != null) setState(() => _nextVisit = picked);
  }

  Future<void> _respond(String answer) async {
    setState(() {
      _saving = true;
      _status = null;
    });
    try {
      final date = _nextVisit == null
          ? null
          : '${_nextVisit!.year.toString().padLeft(4, '0')}-'
            '${_nextVisit!.month.toString().padLeft(2, '0')}-'
            '${_nextVisit!.day.toString().padLeft(2, '0')}';
      final result = await EmailConfirmationService(
        baseUrl: widget.apiBaseUrl,
      ).respond(
        token: widget.invitationToken,
        answer: answer,
        nextVisitDate: date,
      );
      setState(() => _status = result['message']?.toString() ?? 'Response saved.');
    } catch (e) {
      setState(() => _status = 'Error: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Visit Confirmation')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Can you attend the planned visit?',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _chooseDate,
              icon: const Icon(Icons.calendar_month),
              label: Text(_nextVisit == null
                  ? 'Choose next visit date (optional)'
                  : 'Next visit: ${_nextVisit!.day}/${_nextVisit!.month}/${_nextVisit!.year}'),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _saving ? null : () => _respond('YES'),
              child: const Text('YES, I can attend'),
            ),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: _saving ? null : () => _respond('NO'),
              child: const Text('NO, I cannot attend'),
            ),
            if (_status != null) ...[
              const SizedBox(height: 16),
              SelectableText(_status!),
            ],
          ],
        ),
      ),
    );
  }
}
