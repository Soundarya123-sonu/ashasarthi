import 'package:flutter/material.dart';
import 'email_confirmation_service.dart';

class EmailConfirmationScreen extends StatefulWidget {
  const EmailConfirmationScreen({
    super.key,
    required this.apiBaseUrl,
    required this.workerName,
  });

  final String apiBaseUrl;
  final String workerName;

  @override
  State<EmailConfirmationScreen> createState() => _EmailConfirmationScreenState();
}

class _EmailConfirmationScreenState extends State<EmailConfirmationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _message = TextEditingController(
    text: 'Please confirm your upcoming visit.',
  );
  DateTime? _visitDate;
  bool _sending = false;
  String? _result;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _message.dispose();
    super.dispose();
  }

  Future<void> _chooseDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _visitDate ?? now,
      firstDate: DateTime(now.year, now.month, now.day),
      lastDate: DateTime(now.year + 3),
    );
    if (picked != null) setState(() => _visitDate = picked);
  }

  Future<void> _send() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _sending = true;
      _result = null;
    });

    try {
      final date = _visitDate == null
          ? null
          : '${_visitDate!.year.toString().padLeft(4, '0')}-'
            '${_visitDate!.month.toString().padLeft(2, '0')}-'
            '${_visitDate!.day.toString().padLeft(2, '0')}';
      final result = await EmailConfirmationService(
        baseUrl: widget.apiBaseUrl,
      ).sendVisitEmail(
        beneficiaryName: _name.text.trim(),
        beneficiaryEmail: _email.text.trim(),
        workerName: widget.workerName,
        message: _message.text.trim(),
        proposedVisitDate: date,
      );
      setState(() => _result = result['message']?.toString() ?? 'Email sent.');
    } catch (e) {
      setState(() => _result = 'Error: $e');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Beneficiary Visit Email')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Send a visit confirmation request to the beneficiary.',
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(
                    labelText: 'Beneficiary name',
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Enter beneficiary name'
                      : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Beneficiary email',
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) {
                    if (v == null || !RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v.trim())) {
                      return 'Enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _message,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Email message',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: _chooseDate,
                  icon: const Icon(Icons.calendar_month),
                  label: Text(_visitDate == null
                      ? 'Choose proposed visit date'
                      : 'Visit date: ${_visitDate!.day}/${_visitDate!.month}/${_visitDate!.year}'),
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _sending ? null : _send,
                  icon: _sending
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.email_outlined),
                  label: Text(_sending ? 'Sending...' : 'Send confirmation email'),
                ),
                if (_result != null) ...[
                  const SizedBox(height: 16),
                  SelectableText(_result!),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
