# SPACE-JET
A 2D space shooter built with Pygame for desktop and mobile devices. Features 50 progressive 60-second timed survival levels. Includes dynamic background themes and scaling enemy speeds. Face diverse space hazards like asteroids, comets, and alien craft. Pilot your starship using keyboard or touch screen controls. Automatically saves level progress

# Cosmic Defender — Android APK

This folder contains the Android-ready version of the Pygame game.

## Features included

- 50 levels.
- Progress saved in Android private app storage.
- Progress is restored after closing/reopening the app.
- Autosaves every 2 seconds during play.
- Saves when the Android app loses focus.
- Existing leaderboard entries are never deleted.
- Leaderboard keeps each player's best level and best score.
- Touch controls: drag your finger to move the ship; tap to shoot.
- Android Back pauses the game first and then navigates back through menus.
- Background music with an in-game sound toggle.
- Multiple space-object shapes and changing backgrounds.
- Moon journey after each 60-second level.
- Initial supplied progress/leaderboard files are copied only on first run and never overwrite existing saved data.

## Build the APK

Use Linux/WSL with Java, Android build tools, Python, and Buildozer installed.

```bash
cd cosmic_defender_android
buildozer android debug
```

The debug APK will be placed in the `bin/` folder.

For a release APK:

```bash
buildozer android release
```

The first build downloads the Android SDK/NDK and may take a while.

## Windows users

The most reliable Buildozer setup is WSL2 (Ubuntu). Copy this folder into the WSL filesystem, install Buildozer there, then run the command above.

## Important save behavior

`cosmic_progress.json` and `leaderboard.json` included in the APK are only first-run defaults. During play, Android writes the live copies to the app's private writable storage. Closing the app does not reset the level. Uninstalling the app normally removes its private data, as with other Android apps.
