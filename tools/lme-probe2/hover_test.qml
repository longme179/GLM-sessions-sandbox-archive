//@ pragma AppId lme-hovertest
//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
// Agent-2 probe (scratch copy only): which items see the pointer over real controls?
import QtQuick
import QtQuick.Controls
import Quickshell
import "qml/components"
import "qml/theme"

FloatingWindow {
    id: win
    width: 600
    height: 320
    color: "#202020"

    Item {
        id: root
        anchors.fill: parent
        function log(line) { console.warn("@@HOVER " + line); }

        // Candidate A: hover-enabled, button-less MouseArea declared first (bottom of the stack).
        MouseArea {
            id: bottom
            anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton
            onPositionChanged: root.log("bottom.move " + Math.round(mouseX) + "," + Math.round(mouseY))
        }
        // Candidate B: a non-blocking HoverHandler on the root; its point is polled below.
        HoverHandler { id: watch }

        Column {
            x: 20; y: 20; spacing: 16
            LiquidButton { id: btn; width: 240; text: "LiquidButton"; onClicked: root.log("btn.clicked") }
            ExpressiveField { id: field; width: 240; placeholderText: "ExpressiveField"
                onAccepted: root.log("field.accepted") }
            LiquidSlider { id: slider; width: 240 }
            Button { id: plain; width: 240; hoverEnabled: true; text: "Plain Button"; onClicked: root.log("plain.clicked") }
            Rectangle { id: area; width: 240; height: 40; color: "#404040"
                MouseArea { id: areaHover; anchors.fill: parent; hoverEnabled: true
                    onPositionChanged: root.log("area.move " + Math.round(mouseX) + "," + Math.round(mouseY)) } }
        }
        Rectangle { x: 400; y: 20; width: 180; height: 280; color: "transparent" }

        Timer {
            interval: 100; repeat: true; running: true
            property real lx: -1
            property real ly: -1
            onTriggered: {
                const p = watch.point.position;
                if (p.x !== lx || p.y !== ly) {
                    lx = p.x; ly = p.y;
                    root.log("watch.sample " + p.x.toFixed(1) + "," + p.y.toFixed(1)
                             + " hovered=" + watch.hovered + " btn=" + btn.hovered
                             + " field=" + field.hovered + " slider=" + slider.hovered
                             + " plain=" + plain.hovered + " area=" + areaHover.containsMouse);
                }
            }
        }
    }
}
