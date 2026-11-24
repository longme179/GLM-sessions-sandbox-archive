//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import "qml/components"
import "qml/services"
import "qml/settings"
ShellRoot {
    FloatingWindow {
        id: win; implicitWidth: 1200; implicitHeight: 900; color: "black"
        Item { id: host; anchors.fill: parent }
        property var specs: [
            ["Rectangle", rect], ["LabelText", label], ["LiquidButton", button], ["IconButton", icon], ["ExpressiveSwitch", sw],
            ["LiquidSlider", slider], ["LiquidComboBox", combo], ["GlassPanel", glass], ["GlassMaterial", gm], ["LiquidFeedback", fb], ["MotionValue", mv], ["PreferenceSwitch", pref], ["SettingsCard", card]]
        Component { id: rect; Rectangle { width: 40; height: 40; radius: 8 } }
        Component { id: label; LabelText { text: "Hello world" } }
        Component { id: button; LiquidButton { text: "Button" } }
        Component { id: icon; IconButton { glyph: "×" } }
        Component { id: sw; ExpressiveSwitch {} }
        Component { id: slider; LiquidSlider {} }
        Component { id: combo; LiquidComboBox { model: ["a", "b"] } }
        Component { id: glass; GlassPanel { width: 100; height: 100 } }
        Component { id: gm; GlassMaterial { width: 40; height: 40 } }
        Component { id: fb; LiquidFeedback { width: 40; height: 40 } }
        Component { id: mv; MotionValue { target: 1 } }
        Component { id: pref; PreferenceSwitch {} }
        Component { id: card; SettingsCard { } }
        Timer {
            interval: 4000; running: ShellState.backendReady || true; onTriggered: {
                for (const [name, c] of win.specs) {
                    for (let warm = 0; warm < 2; ++warm) {
                        const objs = []; const t = Date.now();
                        for (let i = 0; i < 50; ++i) objs.push(c.createObject(host, {x: (i % 25) * 45, y: Math.floor(i / 25) * 45}));
                        const dt = Date.now() - t;
                        if (warm) console.warn("BENCH " + name + " " + (dt / 50).toFixed(2) + " ms/each" + (objs[0] ? "" : " (null)"));
                        for (const o of objs) if (o) o.destroy();
                    }
                }
                Qt.quit();
            }
        }
    }
}
