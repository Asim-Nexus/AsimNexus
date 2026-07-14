"""
STATUS: REAL — AsimBrain Module

AsimNexus AsimBrain
====================
Core brain module with inline Dharma pattern blocking.
Provides DHARMA_BLOCKED_PATTERNS for content filtering.
"""

# Dharma-blocked patterns that are rejected before reaching the LLM
DHARMA_BLOCKED_PATTERNS = {
    # English harmful patterns
    "make bomb",
    "kill people",
    "how to hack",
    "steal data",
    "credit card fraud",
    "identity theft",
    "malware creation",
    "ransomware",
    "terrorist attack",
    "weapon instructions",
    "drug synthesis",
    "poison recipe",
    "exploit vulnerability",
    "ddos attack",
    "phishing kit",
    "child exploitation",
    "human trafficking",
    "money laundering",
    "tax evasion scheme",
    "fraudulent document",
    # Nepali harmful patterns
    "बम बनाउ",
    "मान्छे मार",
    "ह्याक कसरी गर्ने",
    "डाटा चोरी",
    "क्रेडिट कार्ड धोखाधडी",
    "पहिचान चोरी",
    "मालवेयर सिर्जना",
    "आतंकवादी आक्रमण",
    "हतियार निर्देशन",
    "लागूऔषध संश्लेषण",
    "विष नुस्खा",
    "शोषण",
    "मानव तस्करी",
    "मनी लान्ड्रिङ",
    "कर छली योजना",
    "जाली दस्तावेज",
}
