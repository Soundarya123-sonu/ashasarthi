
import 'package:flutter/material.dart';

class EmailAvailabilityScreen extends StatefulWidget {
  const EmailAvailabilityScreen({super.key});

  @override
  State<EmailAvailabilityScreen> createState() =>
      _EmailAvailabilityScreenState();
}

class _EmailAvailabilityScreenState
    extends State<EmailAvailabilityScreen> {
  String? availability;
  DateTime? nextVisitDate;

  Future<void> selectDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(
        const Duration(days: 1),
      ),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(
        const Duration(days: 365),
      ),
    );

    if (date != null) {
      setState(() => nextVisitDate = date);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Visit Availability'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Are you available today?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            RadioListTile<String>(
              title: const Text('Yes, I am available'),
              value: 'Yes',
              groupValue: availability,
              onChanged: (value) {
                setState(() {
                  availability = value;
                  nextVisitDate = null;
                });
              },
            ),

            RadioListTile<String>(
              title: const Text('No, I am unavailable'),
              value: 'No',
              groupValue: availability,
              onChanged: (value) {
                setState(() => availability = value);
              },
            ),

            if (availability == 'No') ...[
              const SizedBox(height: 20),
              const Text(
                'Select your next visit date',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: selectDate,
                icon: const Icon(Icons.calendar_month),
                label: Text(
                  nextVisitDate == null
                      ? 'Choose next visit date'
                      : '${nextVisitDate!.day}/'
                        '${nextVisitDate!.month}/'
                        '${nextVisitDate!.year}',
                ),
              ),
            ],

            const Spacer(),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  if (availability == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          'Please select Yes or No',
                        ),
                      ),
                    );
                    return;
                  }

                  if (availability == 'No' &&
                      nextVisitDate == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          'Please select the next visit date',
                        ),
                      ),
                    );
                    return;
                  }

                  final date = nextVisitDate == null
                      ? 'Not required'
                      : '${nextVisitDate!.day}/'
                        '${nextVisitDate!.month}/'
                        '${nextVisitDate!.year}';

                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        'Availability: $availability | '
                        'Next visit: $date',
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.check_circle),
                label: const Text('Submit Availability'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
