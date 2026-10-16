from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from patients.models import Patient

PASSWORD = "StrongPass@123"

PATIENT_PAYLOAD = {
    "name": "Ramesh Kumar",
    "age": 45,
    "gender": "male",
    "phone": "9876543210",
    "address": "Jaipur",
    "medical_history": "Diabetes",
}

DOCTOR_PAYLOAD = {
    "name": "Anita Sharma",
    "specialization": "Cardiology",
    "email": "anita@hospital.com",
    "phone": "9999900001",
    "experience_years": 12,
}


class APIBase(APITestCase):
    def make_user(self, email, name="Test User"):
        return User.objects.create_user(
            username=email, email=email, password=PASSWORD, first_name=name
        )

    def login_as(self, user):
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def make_patient(self, owner, name="Ramesh Kumar"):
        return Patient.objects.create(
            owner=owner, name=name, age=45, gender="male"
        )

    def make_doctor(self, email="anita@hospital.com", name="Anita Sharma"):
        return Doctor.objects.create(
            name=name,
            specialization="Cardiology",
            email=email,
            experience_years=10,
        )


class AuthTests(APIBase):
    def test_register_success(self):
        response = self.client.post(
            "/api/auth/register/",
            {"name": "A User", "email": "a@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data["user"])
        user = User.objects.get(email="a@example.com")
        self.assertNotEqual(user.password, PASSWORD)  # stored hashed
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_duplicate_email(self):
        self.make_user("a@example.com")
        response = self.client.post(
            "/api/auth/register/",
            {"name": "Again", "email": "A@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_email_and_missing_fields(self):
        bad_email = self.client.post(
            "/api/auth/register/",
            {"name": "X", "email": "not-an-email", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(bad_email.status_code, 400)
        missing = self.client.post(
            "/api/auth/register/", {"email": "x@example.com"}, format="json"
        )
        self.assertEqual(missing.status_code, 400)

    def test_login_success(self):
        user = self.make_user("a@example.com")
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        user = self.make_user("a@example.com")
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "WrongPass@999"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoints_require_token(self):
        for url in [
            "/api/patients/",
            "/api/doctors/",
            "/api/mappings/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 401)


class PatientTests(APIBase):
    def setUp(self):
        self.user = self.make_user("owner@example.com")
        self.other = self.make_user("other@example.com")
        self.login_as(self.user)

    def test_create_patient(self):
        response = self.client.post(
            "/api/patients/", PATIENT_PAYLOAD, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Patient.objects.get(pk=response.data["id"]).owner, self.user
        )

    def test_create_patient_invalid(self):
        response = self.client.post(
            "/api/patients/", {"name": "No Age"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_list_only_own_patients(self):
        self.make_patient(self.user)
        self.make_patient(self.other, name="Not Mine")
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Ramesh Kumar")

    def test_retrieve_update_delete_own_patient(self):
        patient = self.make_patient(self.user)
        url = f"/api/patients/{patient.id}/"
        self.assertEqual(self.client.get(url).status_code, 200)

        updated = dict(PATIENT_PAYLOAD, age=46)
        response = self.client.put(url, updated, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["age"], 46)

        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_cannot_access_other_users_patient(self):
        patient = self.make_patient(self.other, name="Not Mine")
        url = f"/api/patients/{patient.id}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.put(url, PATIENT_PAYLOAD, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(Patient.objects.filter(pk=patient.id).exists())


class DoctorTests(APIBase):
    def setUp(self):
        self.user = self.make_user("owner@example.com")
        self.login_as(self.user)

    def test_create_doctor(self):
        response = self.client.post(
            "/api/doctors/", DOCTOR_PAYLOAD, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_duplicate_doctor_email(self):
        self.make_doctor()
        response = self.client.post(
            "/api/doctors/", DOCTOR_PAYLOAD, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_list_retrieve_update_delete_doctor(self):
        doctor = self.make_doctor()
        self.assertEqual(len(self.client.get("/api/doctors/").data), 1)

        url = f"/api/doctors/{doctor.id}/"
        self.assertEqual(self.client.get(url).status_code, 200)

        updated = dict(DOCTOR_PAYLOAD, experience_years=13)
        response = self.client.put(url, updated, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["experience_years"], 13)

        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_nonexistent_doctor(self):
        self.assertEqual(self.client.get("/api/doctors/9999/").status_code, 404)


class MappingTests(APIBase):
    def setUp(self):
        self.user = self.make_user("owner@example.com")
        self.other = self.make_user("other@example.com")
        self.patient = self.make_patient(self.user)
        self.doctor = self.make_doctor()
        self.login_as(self.user)

    def create_mapping(self, patient_id, doctor_id):
        return self.client.post(
            "/api/mappings/",
            {"patient": patient_id, "doctor": doctor_id},
            format="json",
        )

    def test_create_mapping(self):
        response = self.create_mapping(self.patient.id, self.doctor.id)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_duplicate_mapping(self):
        self.create_mapping(self.patient.id, self.doctor.id)
        response = self.create_mapping(self.patient.id, self.doctor.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_invalid_patient_or_doctor_id(self):
        self.assertEqual(
            self.create_mapping(9999, self.doctor.id).status_code, 400
        )
        self.assertEqual(
            self.create_mapping(self.patient.id, 9999).status_code, 400
        )

    def test_cannot_map_other_users_patient(self):
        others_patient = self.make_patient(self.other, name="Not Mine")
        response = self.create_mapping(others_patient.id, self.doctor.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PatientDoctorMapping.objects.count(), 0)

    def test_list_mappings_only_own(self):
        PatientDoctorMapping.objects.create(
            patient=self.patient, doctor=self.doctor
        )
        self.assertEqual(len(self.client.get("/api/mappings/").data), 1)
        self.login_as(self.other)
        self.assertEqual(len(self.client.get("/api/mappings/").data), 0)

    def test_doctors_assigned_to_patient(self):
        PatientDoctorMapping.objects.create(
            patient=self.patient, doctor=self.doctor
        )
        response = self.client.get(f"/api/mappings/{self.patient.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["doctors"]), 1)
        self.assertEqual(response.data["doctors"][0]["id"], self.doctor.id)

        self.login_as(self.other)
        response = self.client.get(f"/api/mappings/{self.patient.id}/")
        self.assertEqual(response.status_code, 404)

    def test_delete_mapping(self):
        mapping = PatientDoctorMapping.objects.create(
            patient=self.patient, doctor=self.doctor
        )
        url = f"/api/mappings/{mapping.id}/"

        self.login_as(self.other)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(PatientDoctorMapping.objects.filter(pk=mapping.id).exists())

        self.login_as(self.user)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.delete(url).status_code, 404)
