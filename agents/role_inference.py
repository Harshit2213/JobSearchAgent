from agents.base import BaseAgent
from models.resume import ParsedResume

_INFER_TOOL = {
    "name": "infer_roles",
    "description": "Suggest the most suitable job role titles for a candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "roles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3 to 5 role titles, most suitable first",
            }
        },
        "required": ["roles"],
    },
}

_SYSTEM = (
    "You are a career advisor. Based on the candidate profile, suggest 3 to 5 specific job roles "
    "they are most qualified for. Consider their experience level, tech stack, and past titles. "
    "Return concrete, searchable role titles such as 'Senior Backend Engineer' or 'ML Engineer'. "
    "Rank from best fit to reasonable stretch."
)


class RoleInferenceAgent(BaseAgent):
    _quality = "fast"
    def infer(self, profile: ParsedResume) -> list[str]:
        profile_text = "\n".join([
            f"Past titles: {', '.join(profile.past_titles) or 'N/A'}",
            f"Years of experience: {profile.years_of_experience}",
            f"Tech stack: {', '.join(profile.tech_stack) or 'N/A'}",
            f"Skills: {', '.join(profile.skills) or 'N/A'}",
            f"Education: {', '.join(profile.education) or 'N/A'}",
            f"Summary: {profile.summary or 'N/A'}",
        ])
        response = self._call(
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Suggest suitable roles:\n\n{profile_text}"}],
            tools=[_INFER_TOOL],
            tool_name="infer_roles",
            cache_system=True,
        )
        data = self._extract_tool_input(response)
        return data.get("roles", [])
