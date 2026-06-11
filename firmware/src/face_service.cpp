// face_service.cpp
// Visuals are intentionally disabled until the final artwork is available.

#include "face_service.h"

#include <M5Unified.h>

static WhaleFace currentFace = WHALE_CALM;

void initFace() {
    M5.Display.fillScreen(TFT_BLACK);
    Serial.println("[FACE] Visuals disabled; display left blank");
}

void setFaceExpression(FaceExpression expr) {
    (void)expr;
}

void setMouthOpen(float ratio) {
    (void)ratio;
}

void setWhaleFace(WhaleFace face) {
    currentFace = face;
}

const char* getCurrentFaceName() {
    return whaleFaceName(currentFace);
}
