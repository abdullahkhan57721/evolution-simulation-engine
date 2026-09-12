import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    required property var theme
    required property var app
    required property var results
    required property var reference
    contentWidth: availableWidth

    ColumnLayout {
        width: root.availableWidth
        spacing: root.theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Results"
            title: "Results"
            description: "Current-session Results are accepted only when existing WB5 ownership semantics match the exact active scientific artifact. Missing evidence is never reconstructed."
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: !root.results.hasResult
            tone: "neutral"
            title: root.app.runReferenceCount > 0 ? "Historical provenance only" : "No current-session result"
            message: root.results.historicalMessage.length > 0
                ? root.results.historicalMessage
                : "Run the exact current Study to produce an authoritative in-session result payload."
            Layout.fillWidth: true
        }

        ResultSection {
            theme: root.theme
            visible: root.results.hasResult
            title: root.results.overviewTitle
            model: root.results.overviewModel
            Layout.fillWidth: true
        }

        ResultSection {
            theme: root.theme
            visible: root.results.hasResult
            title: root.results.exploreTitle
            model: root.results.exploreModel
            Layout.fillWidth: true
        }

        ResultSection {
            theme: root.theme
            visible: root.results.hasResult
            title: root.results.analysisTitle
            model: root.results.analysisModel
            Layout.fillWidth: true
        }

        ResultSection {
            theme: root.theme
            visible: root.results.hasResult
            title: "Provenance"
            model: root.results.provenanceModel
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: root.app.artifactKind === "reference-ecology" && root.reference.hasWorld
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(340, Math.min(430, root.height * 0.55))
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: root.theme.space3
                spacing: root.theme.space2
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Recorded world"
                        color: root.theme.text
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    StatusBadge {
                        theme: root.theme
                        text: "COMMITTED STEP " + root.reference.worldStep
                        tone: "neutral"
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: "Organisms can be selected by pointer or keyboard. Selection is also exposed through accessible state and is never communicated by fill color alone."
                    color: root.theme.subtleText
                    font.pixelSize: root.theme.textSmall
                    wrapMode: Text.Wrap
                }
                Rectangle {
                    id: worldCanvas
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: root.theme.canvasRaised
                    radius: root.theme.radius
                    border.color: root.theme.border
                    clip: true

                    Repeater {
                        model: root.reference.resourceModel
                        delegate: Rectangle {
                            required property real amount
                            required property real worldX
                            required property real worldY
                            width: Math.max(3, Math.min(10, 2 + amount / 4))
                            height: width
                            radius: width / 2
                            color: root.theme.resource
                            opacity: 0.55
                            x: (worldX + 0.5) / Math.max(1, root.reference.worldWidth) * worldCanvas.width - width / 2
                            y: (worldY + 0.5) / Math.max(1, root.reference.worldHeight) * worldCanvas.height - height / 2
                            Accessible.name: "Resource amount " + amount
                            Accessible.role: Accessible.Graphic
                        }
                    }
                    Repeater {
                        model: root.reference.organismModel
                        delegate: Rectangle {
                            id: organismMarker
                            required property int organismId
                            required property real worldX
                            required property real worldY
                            required property real markerSize
                            required property bool selected
                            required property real bodyMass
                            required property real energy
                            width: markerSize
                            height: markerSize
                            radius: width / 2
                            color: selected ? root.theme.selected : root.theme.organism
                            border.width: activeFocus ? 3 : (selected ? 3 : 1)
                            border.color: activeFocus ? root.theme.focus : (selected ? root.theme.warning : root.theme.text)
                            x: (worldX + 0.5) / Math.max(1, root.reference.worldWidth) * worldCanvas.width - width / 2
                            y: (worldY + 0.5) / Math.max(1, root.reference.worldHeight) * worldCanvas.height - height / 2
                            activeFocusOnTab: true
                            Accessible.name: "Organism " + organismId
                            Accessible.description: "Body mass " + bodyMass + ", energy " + energy + (selected ? ". Selected." : ".")
                            Accessible.role: Accessible.Button
                            Accessible.selected: selected
                            Accessible.onPressAction: root.reference.selectOrganism(organismId)
                            Keys.onReturnPressed: root.reference.selectOrganism(organismId)
                            Keys.onEnterPressed: root.reference.selectOrganism(organismId)
                            Keys.onSpacePressed: root.reference.selectOrganism(organismId)
                            ToolTip.visible: hover.hovered
                            ToolTip.text: "Organism " + organismId + " · mass " + bodyMass + " · energy " + energy
                            HoverHandler { id: hover }
                            TapHandler { onTapped: root.reference.selectOrganism(organismId) }
                        }
                    }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.app.artifactKind === "reference-ecology"
                && root.results.hasResult
                && !root.reference.hasWorld
            tone: "neutral"
            title: "No recorded spatial replay in this exact result"
            message: "Spatial history was not recorded for this exact result. Native Results do not reconstruct unrecorded world state; run again with the appropriate EvidencePlan if spatial replay is required."
            Layout.fillWidth: true
        }

        Item { Layout.preferredHeight: root.theme.space4 }
    }
}
