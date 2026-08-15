# Add voice workflow

1. Verify explicit consent, source ownership, allowed purpose, owner and retention policy before ingest.
2. Store original reference and prepared copy separately; do not destructively overwrite either.
3. Measure sample rate, duration, silence, clipping and signal-to-noise quality.
4. Produce a transcript, request human correction, then synthesize a fixed audition text.
5. Record language, quality metrics, consent metadata, reference version and transcript in `VoiceProfile`.
6. Register as `draft`; do not make it a default voice.
7. Require human audition and explicit release approval before stable publication.

Reject unverified web clips, celebrity voices, voice references without consent and incomplete transcript/owner metadata.
