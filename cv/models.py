import json, uuid
from django.db.models import Q
from django.utils import timezone
from typing import Any, Dict, List, Union
from django.db import models, transaction
from django.core.exceptions import ValidationError


class Candidates(models.Model):
    name = models.CharField(max_length=80, null=True, blank=True)
    email = models.CharField(max_length=120, null=True, blank=True)  # optional, unique only when not null
    mobile = models.CharField(max_length=20, null=True, blank=True)

    cv_fileid = models.CharField(null=False, unique=True, max_length=255, editable=False)
    cv_filename = models.CharField(null=False, blank=False, max_length=255)

    # Store skills as a list (cleaner than comma-separated text)
    skills = models.JSONField(null=True, blank=True, default=list)
    total_exp = models.IntegerField(null=True, blank=True)

    ollama = models.JSONField(null=True, default=None, blank=True)
    ollama_gen_time = models.DateTimeField(null=True, default=None, blank=True)

    openai = models.JSONField(null=True, default=None, blank=True)
    openai_gen_time = models.DateTimeField(null=True, default=None, blank=True)

    create_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cv_candidates"
        indexes = [
            models.Index(fields=["email"], name="cv_candidates_idx_email"),
        ]

    def show(self):
        return {
            "id" : self.id, 
            "name" : self.name, 
            "email" : self.email,
            "mobile" : self.mobile,
            "cv_fileid" : self.cv_fileid,
            "cv_filename" : self.cv_filename,
            "skills" : self.skills,
            "total_exp" : self.total_exp,
            "ollama" : self.ollama,
            "ollama_gen_time" : self.ollama_gen_time,
            "openai" : self.openai,
            "openai_gen_time" : self.openai_gen_time,
            "create_time" : self.create_time
        }

    # ---------------------------
    # Skill normalization helpers
    # ---------------------------
    @staticmethod
    def _normalize_skill(s: str) -> str:
        return " ".join((s or "").strip().split()).lower()

    @staticmethod
    def _pretty_skill(s: str) -> str:
        return " ".join((s or "").strip().split())

    @classmethod
    @transaction.atomic
    def create_record(cls, fileid: str, filename: str) -> "Candidates":
        if not fileid:
            raise ValidationError("fileid is required")
        if not filename or not str(filename).strip():
            raise ValidationError("filename is required")

        return cls.objects.create(
            cv_fileid=fileid,
            cv_filename=str(filename).strip(),
        )

    @classmethod
    @transaction.atomic
    def update_with_llm_json(cls, candidate: "Candidates", payload_json: Union[str, Dict[str, Any]], llm: str ) -> "Candidates":
        """
        Updates the SAME candidate row that was created with (cv_fileid + cv_filename).
        No email lookup. No cross-record hijack.
        Concurrency-safe via SELECT ... FOR UPDATE.
        """

        if not candidate or not candidate.pk:
            raise ValidationError("candidate instance must be a saved Candidates object")

        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
        except Exception as e:
            raise ValidationError(f"Invalid JSON payload: {e}")

        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a JSON object")

        # Lock the row for safe concurrent updates
        obj = cls.objects.select_for_update().get(pk=candidate.pk)

        # Extract fields (tolerant, does not force email)
        name = payload.get("candidate_name") or payload.get("candidateName") or payload.get("name")
        email = (payload.get("email") or "").strip().lower() or None
        mobile = payload.get("contact_number") or payload.get("contactNumber") or payload.get("mobile")
        total_exp = payload.get("overall_years_experience")

        # Skills extraction
        skills_list = payload.get("skills") or []
        incoming_skills: List[str] = []

        for s in skills_list:
            if isinstance(s, dict):
                n = cls._pretty_skill(s.get("name") or "")
                if n:
                    incoming_skills.append(n)
            elif isinstance(s, str):
                n = cls._pretty_skill(s)
                if n:
                    incoming_skills.append(n)

        # Merge skills (stable order, case/space-insensitive dedupe)
        existing = obj.skills or []
        if not isinstance(existing, list):
            existing = []

        seen = set()
        merged: List[str] = []

        for s in existing:
            if isinstance(s, str):
                k = cls._normalize_skill(s)
                if k and k not in seen:
                    seen.add(k)
                    merged.append(cls._pretty_skill(s))

        for s in incoming_skills:
            k = cls._normalize_skill(s)
            if k and k not in seen:
                seen.add(k)
                merged.append(s)

        # Assign updated values
        obj.name = name
        obj.email = email
        obj.mobile = mobile

        obj.total_exp = (
            int(total_exp)
            if total_exp is not None and str(total_exp).strip() != ""
            else None
        )

        obj.skills = merged

        now = timezone.now()
        llm_norm = (llm or "").strip().lower()

        if llm_norm == "ollama":
            obj.ollama = payload
            obj.ollama_gen_time = now
        elif llm_norm == "openai":
            obj.openai = payload
            obj.openai_gen_time = now
        else:
            raise ValidationError("llm must be either 'ollama' or 'openai'")

        obj.save()
        return obj
