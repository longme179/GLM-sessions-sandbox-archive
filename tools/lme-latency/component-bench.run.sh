export XDG_RUNTIME_DIR=/tmp/opencode/lat/bench/rt; rm -rf $XDG_RUNTIME_DIR; mkdir -m700 -p $XDG_RUNTIME_DIR
for v in XDG_CONFIG_HOME XDG_STATE_HOME XDG_DATA_HOME XDG_CACHE_HOME; do d=/tmp/opencode/lat/bench/$v; rm -rf $d; mkdir -p $d; export $v=$d; done
unset WAYLAND_DISPLAY DISPLAY NIRI_SOCKET; export LME_SHELL_DEMO=1 WLR_BACKENDS=headless WLR_RENDERER=gles2 WLR_LIBINPUT_NO_DEVICES=1
printf 'xwayland disable\noutput HEADLESS-1 mode 1920x1080@60Hz\n' > sway.conf
sway --config sway.conf > sway.log 2>&1 & sleep 1; export WAYLAND_DISPLAY=wayland-1
timeout 60 quickshell -p /tmp/opencode/lat/bench/shell.qml 2>&1 | grep -E "BENCH|ERROR|rror" | head -30
kill %1
