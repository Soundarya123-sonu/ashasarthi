
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:sqflite_common/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/supervisor_dashboard_screen.dart';
import 'screens/beneficiary_screen.dart';
import 'screens/messages_screen.dart';
import 'screens/notifications_screen.dart';
import 'screens/language_screen.dart';
import 'services/language_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  debugPrint('AshaSarthi: Initializing application...');

  try {
    // Initialize SQLite for Flutter Web only.
    if (kIsWeb) {
      databaseFactory = databaseFactoryFfiWeb;
    }

    debugPrint('Before language load');
await LanguageService.load();
debugPrint('After language load');

    debugPrint('AshaSarthi: Language loaded successfully.');
  } catch (error, stackTrace) {
    debugPrint('AshaSarthi startup error: $error');
    debugPrintStack(stackTrace: stackTrace);
  }

  debugPrint('AshaSarthi: Calling runApp().');
  runApp(const AshaSarthiApp());
}

class AshaSarthiApp extends StatelessWidget {
  const AshaSarthiApp({super.key});

  @override
  Widget build(BuildContext context) {
    debugPrint('AshaSarthi: Building application UI.');

    return ValueListenableBuilder<String>(
      valueListenable: LanguageService.language,
      builder: (context, language, _) {
        final localeCode = language == 'मराठी'
            ? 'mr'
            : language == 'हिन्दी'
                ? 'hi'
                : 'en';

        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: 'AshaSarthi',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.teal,
            ),
            useMaterial3: true,
            scaffoldBackgroundColor: const Color(0xFFF4F7FB),
          ),
          locale: Locale(localeCode),
          home: const LoginScreen(),
          routes: {
            '/login': (_) => const LoginScreen(),
            '/register': (_) => const RegisterScreen(),
            '/asha-dashboard': (_) => DashboardScreen(),
            '/supervisor-dashboard': (_) =>
                SupervisorDashboardScreen(),
            '/beneficiary-dashboard': (_) =>
                BeneficiaryScreen(),
            '/messages': (_) => const MessagesScreen(),
            '/notifications': (_) =>
                const NotificationsScreen(),
            '/language': (_) => const LanguageScreen(),
          },
        );
      },
    );
  }
}
