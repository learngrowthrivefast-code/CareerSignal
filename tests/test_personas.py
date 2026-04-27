"""
CareerSignal — Three Persona Quality Tests

Persona 1 · Fresh Graduate (Age 20-35)
  Motivation: Land first real role; grow to Senior or Staff Engineer
  Risk profile: Low experience, high speed, portfolio-first

Persona 2 · Mid-career (Age 35-50)
  Motivation: Transition from Senior IC to Solutions Architect or Senior Manager
  Risk profile: Deep technical expertise, needs to shift identity from doer to leader

Persona 3 · Industry Veteran (Age 50+)
  Motivation: Reach Director, VP, SVP, or CTO
  Risk profile: Risk of being overlooked for age/recency; scar tissue is the real asset
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.prompt_builder import build_system_prompt, _role_tier
from core.auth import hash_password, verify_password, create_token, decode_token
from config.settings import COHORTS, TARGET_ROLES


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA 1 — Fresh Graduate · Age 20-35 · Senior/Staff Engineer target
# ═══════════════════════════════════════════════════════════════════════════
class TestFreshGraduatePersona:
    """
    Zara Ahmed, 24.
    Junior Data Analyst at a startup. Self-taught ML background, 3 GitHub projects.
    Wants to become a Senior ML Engineer within 2 years.
    Fear: Not enough formal experience compared to candidates with 5+ years.
    """

    PROFILE = {
        "name":         "Zara Ahmed",
        "cohort":       "FreshGraduate",
        "current_role": "Junior Data Analyst",
        "target_role":  "Senior ML Engineer",
        "biggest_asset": "3 open-source ML projects with 800+ GitHub stars; shipped production recommendation system",
        "biggest_fear":  "I have no formal CS degree and only 18 months of industry experience",
        "tier":         "free",
        "user_id":      "test-fresh-001",
    }

    def test_cohort_is_recognised(self):
        assert self.PROFILE["cohort"] in COHORTS, \
            f"Cohort '{self.PROFILE['cohort']}' missing from COHORTS in settings.py"
        label = COHORTS[self.PROFILE["cohort"]]
        assert "20" in label or "Fresh" in label, \
            f"Cohort label '{label}' should reference age 20-35 or Fresh Builder"

    def test_target_role_is_in_settings(self):
        assert self.PROFILE["target_role"] in TARGET_ROLES, (
            f"'{self.PROFILE['target_role']}' not in TARGET_ROLES. "
            f"Add it to TARGET_ROLES_SENIOR_IC in config/settings.py"
        )

    def test_role_tier_classified_as_senior_ic(self):
        tier = _role_tier(self.PROFILE["target_role"])
        assert tier == "senior_ic", (
            f"'{self.PROFILE['target_role']}' should classify as 'senior_ic', got '{tier}'"
        )

    def test_prompt_contains_fresh_builder_cohort_guidance(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "Fresh Builder" in prompt or "20–35" in prompt, \
            "Prompt missing Fresh Builder cohort guidance"

    def test_prompt_emphasises_portfolio_and_ownership(self):
        prompt = build_system_prompt(self.PROFILE, [])
        keywords = ["portfolio", "ownership", "speed", "mentor"]
        assert any(k in prompt.lower() for k in keywords), (
            f"Senior IC prompt should mention portfolio/ownership/speed/mentor. "
            f"Got prompt starting with: {prompt[:200]}"
        )

    def test_prompt_uses_senior_ic_methodology(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "SENIOR IC TRACK" in prompt, \
            "Fresh graduate targeting a Senior role should receive SENIOR IC TRACK methodology"

    def test_prompt_contains_user_name_and_roles(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert self.PROFILE["name"] in prompt
        assert self.PROFILE["current_role"] in prompt
        assert self.PROFILE["target_role"] in prompt

    def test_prompt_surfaces_users_fear(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "degree" in prompt.lower() or "experience" in prompt.lower(), \
            "User's stated fear should appear in the prompt so the coach can address it"

    def test_past_context_injected_into_prompt(self):
        past = ["User: How do I prove myself without a CS degree? | Coach: Ship things. A portfolio speaks louder."]
        prompt = build_system_prompt(self.PROFILE, past)
        assert "portfolio" in prompt.lower(), \
            "Past coaching context should be injected into the system prompt"

    def test_star_stories_injected_when_provided(self):
        stories = ["STAR: Built recommendation engine. Result: 22% CTR improvement."]
        prompt = build_system_prompt(self.PROFILE, [], star_stories=stories)
        assert "recommendation" in prompt.lower() or "STAR" in prompt, \
            "STAR stories should appear in the prompt when provided"


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA 2 — Mid-career · Age 35-50 · Architect / Senior Manager target
# ═══════════════════════════════════════════════════════════════════════════
class TestMidCareerPersona:
    """
    Carlos Rivera, 41.
    Senior Software Engineer with 14 years experience. Led monolith-to-microservices migration.
    Wants to become a Solutions Architect. Comfortable with both code and stakeholders.
    Fear: Too hands-on / too technical — doesn't know how to position for Architect.
    """

    PROFILE = {
        "name":         "Carlos Rivera",
        "cohort":       "AgeAbove35Less50",
        "current_role": "Senior Software Engineer",
        "target_role":  "Solutions Architect",
        "biggest_asset": "Led migration of monolith to microservices across 4 teams; 10 years cross-stack",
        "biggest_fear":  "I'm too hands-on. I don't know how to position for Architect without giving up coding.",
        "tier":         "free",
        "user_id":      "test-mid-001",
    }

    def test_cohort_is_recognised(self):
        assert self.PROFILE["cohort"] in COHORTS, \
            f"Cohort '{self.PROFILE['cohort']}' missing from COHORTS"
        label = COHORTS[self.PROFILE["cohort"]]
        assert "35" in label or "Bridge" in label, \
            f"Cohort label '{label}' should reference age 35-50 or Bridge Builder"

    def test_target_role_is_in_settings(self):
        assert self.PROFILE["target_role"] in TARGET_ROLES, (
            f"'{self.PROFILE['target_role']}' not in TARGET_ROLES. "
            f"Add it to TARGET_ROLES_LEADERSHIP in config/settings.py"
        )

    def test_role_tier_classified_as_leadership(self):
        tier = _role_tier(self.PROFILE["target_role"])
        assert tier == "leadership", (
            f"'{self.PROFILE['target_role']}' should classify as 'leadership', got '{tier}'"
        )

    def test_prompt_contains_bridge_builder_cohort_guidance(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "Bridge Builder" in prompt or "35–50" in prompt, \
            "Prompt missing Bridge Builder cohort guidance"

    def test_prompt_emphasises_strategic_influence(self):
        prompt = build_system_prompt(self.PROFILE, [])
        keywords = ["permission", "strategic", "influence", "proactive", "both"]
        assert any(k in prompt.lower() for k in keywords), (
            "Mid-career prompt should push toward strategic influence, not waiting for permission"
        )

    def test_prompt_uses_leadership_methodology(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "LEADERSHIP TRACK" in prompt, \
            "Mid-career targeting Architect/Manager should receive LEADERSHIP TRACK methodology"

    def test_prompt_contains_user_name_and_roles(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert self.PROFILE["name"] in prompt
        assert self.PROFILE["current_role"] in prompt
        assert self.PROFILE["target_role"] in prompt

    def test_prompt_surfaces_identity_transition_fear(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "hands-on" in prompt.lower() or "technical" in prompt.lower(), \
            "User's fear about being too hands-on should appear in the prompt"

    def test_engineering_manager_also_classified_as_leadership(self):
        assert _role_tier("Engineering Manager") == "leadership"
        assert _role_tier("Senior Manager of Engineering") == "leadership"

    def test_star_stories_injected_when_provided(self):
        stories = ["STAR: Microservices migration. Led 4 teams. Result: 60% infra cost reduction."]
        prompt = build_system_prompt(self.PROFILE, [], star_stories=stories)
        assert "Microservices" in prompt or "infra" in prompt.lower(), \
            "STAR stories should appear in the prompt"


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA 3 — Industry Veteran · Age 50+ · Director / VP / CTO target
# ═══════════════════════════════════════════════════════════════════════════
class TestIndustryVeteranPersona:
    """
    Dr. Linda Walsh, 54.
    Senior Manager, AI Platform at a financial services firm.
    Shipped AI governance frameworks across 3 enterprise orgs.
    Wants VP of Engineering (AI). Has lived through 3 major tech cycles.
    Fear: Being passed over because younger candidates seem more current on new AI tools.
    """

    PROFILE = {
        "name":         "Dr. Linda Walsh",
        "cohort":       "AgeAbove50",
        "current_role": "Senior Manager, AI Platform",
        "target_role":  "VP of Engineering (AI)",
        "biggest_asset": "Built AI governance frameworks across 3 enterprise orgs; survived dot-com, cloud, and GenAI waves",
        "biggest_fear":  "I'll be passed over because younger candidates seem more current on new AI tools",
        "tier":         "premium",
        "user_id":      "test-veteran-001",
    }

    def test_cohort_is_recognised(self):
        assert self.PROFILE["cohort"] in COHORTS, \
            f"Cohort '{self.PROFILE['cohort']}' missing from COHORTS"
        label = COHORTS[self.PROFILE["cohort"]]
        assert "50" in label or "Navigator" in label, \
            f"Cohort label '{label}' should reference age 50+ or Navigator"

    def test_target_role_is_in_settings(self):
        assert self.PROFILE["target_role"] in TARGET_ROLES, (
            f"'{self.PROFILE['target_role']}' not in TARGET_ROLES. "
            f"Check TARGET_ROLES_EXECUTIVE in config/settings.py"
        )

    def test_role_tier_classified_as_executive(self):
        tier = _role_tier(self.PROFILE["target_role"])
        assert tier == "executive", (
            f"'{self.PROFILE['target_role']}' should classify as 'executive', got '{tier}'"
        )

    def test_prompt_contains_navigator_cohort_guidance(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "Navigator" in prompt or "50+" in prompt or "scar tissue" in prompt.lower(), \
            "Prompt missing Navigator cohort guidance (Navigator / 50+ / scar tissue)"

    def test_prompt_emphasises_experience_as_advantage(self):
        prompt = build_system_prompt(self.PROFILE, [])
        keywords = ["scar tissue", "technology cycles", "cross-cycle", "judgment", "pattern recognition"]
        assert any(k.lower() in prompt.lower() for k in keywords), (
            "Veteran prompt should reframe long experience as cross-cycle judgment advantage"
        )

    def test_prompt_uses_executive_methodology(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "EXECUTIVE TRACK" in prompt, \
            "Veteran targeting VP/Director should receive EXECUTIVE TRACK methodology"

    def test_prompt_contains_user_name_and_roles(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert self.PROFILE["name"] in prompt
        assert self.PROFILE["current_role"] in prompt
        assert self.PROFILE["target_role"] in prompt

    def test_premium_tier_appears_in_prompt(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "premium" in prompt.lower(), \
            "User tier should be included in the prompt"

    def test_fear_of_age_irrelevance_is_in_prompt(self):
        prompt = build_system_prompt(self.PROFILE, [])
        assert "passed over" in prompt.lower() or "younger" in prompt.lower() or "current" in prompt.lower(), \
            "The veteran's fear of age-related irrelevance should appear in the prompt"

    def test_cto_and_svp_also_classified_as_executive(self):
        assert _role_tier("CTO / Chief AI Officer") == "executive"
        assert _role_tier("SVP of Engineering") == "executive"
        assert _role_tier("Director of AI") == "executive"

    def test_past_context_shapes_prompt(self):
        past = ["User: Am I too old? | Coach: You have cross-cycle judgment no junior engineer can replicate."]
        prompt = build_system_prompt(self.PROFILE, past)
        assert "cross-cycle" in prompt.lower() or "judgment" in prompt.lower()


# ═══════════════════════════════════════════════════════════════════════════
# SHARED — Auth flow works identically for all three personas
# ═══════════════════════════════════════════════════════════════════════════
class TestAuthSharedAcrossPersonas:

    @pytest.mark.parametrize("password", ["SecurePass123!", "AnotherPass99#", "Str0ng&Safe"])
    def test_password_hash_and_verify(self, password):
        hashed = hash_password(password)
        assert verify_password(password, hashed), "Correct password should verify"
        assert not verify_password("WrongPassword!", hashed), "Wrong password should not verify"

    @pytest.mark.parametrize("tier", ["free", "premium"])
    def test_token_roundtrip_for_both_tiers(self, tier):
        token   = create_token("user-abc", "user@test.com", tier)
        payload = decode_token(token)
        assert payload is not None
        assert payload["user_id"] == "user-abc"
        assert payload["email"]   == "user@test.com"
        assert payload["tier"]    == tier

    def test_expired_token_returns_none(self):
        import jwt
        from datetime import datetime, timedelta
        from config.settings import JWT_SECRET, JWT_ALGORITHM
        expired = jwt.encode(
            {"user_id": "x", "email": "x@x.com", "tier": "free",
             "exp": datetime.utcnow() - timedelta(hours=1)},
            JWT_SECRET, algorithm=JWT_ALGORITHM
        )
        assert decode_token(expired) is None, "Expired token should return None"

    def test_tampered_token_returns_none(self):
        token   = create_token("user-abc", "user@test.com", "free")
        tampered = token[:-4] + "XXXX"
        assert decode_token(tampered) is None, "Tampered token should return None"
