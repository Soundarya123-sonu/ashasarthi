class ServerConfig {
  static const String baseUrl =
      'https://ashasarthi-vqv4.onrender.com';

  /// Compile-time configuration only. Do not embed a production server secret
  /// in a mobile app; users can extract values from the app binary.
  /// Use this only for local/prototype testing while replacing shared-key
  /// client authentication with per-user authentication.
  static const String prototypeSyncToken =
      String.fromEnvironment('PROTOTYPE_SYNC_TOKEN');
}