#pragma once
#include "types.h"

void initPlayback();                 // setup()で呼ぶ
void startPlayback(const AudioTask& task);  // ダウンロードキューに積む
void checkPendingPlayback();         // loop()で呼ぶ（Speaker起動）
bool downloadVoice(const String& url, uint8_t** outData, size_t* outSize);
enum PcmPlaybackResult {
    PCM_PLAYBACK_OK,
    PCM_PLAYBACK_QUEUED,
    PCM_PLAYBACK_BUSY,
    PCM_PLAYBACK_SESSION_MISMATCH,
    PCM_PLAYBACK_INVALID,
    PCM_PLAYBACK_SPEAKER_FAILED,
};
PcmPlaybackResult startPcmPlayback(uint8_t* pcmData, size_t pcmSize, const String& sessionId, bool finalSegment);
void clearQueuedPcmPlayback();
void processAudioQueue();
void updateLipSync();
