from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from academics.models import Subject
from evaluations.models import StudentPerformanceMetrics
from users.models import Student, User


class GradePredictionSystem:
    def __init__(self) -> None:
        self.subject_models: dict[int, RegressorMixin] = {}
        self.overall_model: RegressorMixin | None = None
        self.scaler: StandardScaler = StandardScaler()
        self.feature_importance: dict[str, float] = {}

    def prepare_training_data(self) -> pd.DataFrame:
        """Prepare training data including derived features."""

        metrics: Any = StudentPerformanceMetrics.objects.all().select_related(
            "student", "subject"
        )

        base_data: pd.DataFrame = pd.DataFrame.from_records(metrics.values())

        training_data: pd.DataFrame = pd.DataFrame(
            {
                "student_id": base_data["student_id"],
                "subject_id": base_data["subject_id"],
                "attendance_rate": base_data["attendance_rate"],
                "assignment_completion_rate": base_data["assignment_completion_rate"],
                "average_assignment_score": base_data["average_assignment_score"],
                "mid_term_grade": base_data["mid_term_grade"].fillna(0),
                "final_grade": base_data["average_assignment_score"],
            }
        )

        training_data["submission_timeliness"] = 0.0
        training_data["consistency_score"] = (
            training_data.groupby("student_id")["average_assignment_score"]
            .transform("std")
            .fillna(0)
        )

        return training_data

    def train_models(self, training_data: pd.DataFrame | None = None) -> None:
        """Train prediction models using historical data."""
        if training_data is None:
            training_data = self.prepare_training_data()

        feature_columns: list[str] = [
            "attendance_rate",
            "assignment_completion_rate",
            "average_assignment_score",
            "mid_term_grade",
            "submission_timeliness",
            "consistency_score",
        ]

        for subject_id in training_data["subject_id"].unique():
            subject_data: pd.DataFrame = training_data[
                training_data["subject_id"] == subject_id
            ]
            if len(subject_data) > 5:
                X: np.ndarray = subject_data[feature_columns].values
                y: np.ndarray = subject_data["final_grade"].values

                model: RandomForestRegressor = RandomForestRegressor(n_estimators=100)
                model.fit(self.scaler.fit_transform(X), y)
                self.subject_models[subject_id] = model

        X = training_data[feature_columns].values
        y = training_data["final_grade"].values

        self.overall_model = RandomForestRegressor(n_estimators=100)
        self.overall_model.fit(self.scaler.fit_transform(X), y)

    def prepare_student_features(self, student: Student) -> dict[str, float] | None:
        """Prepare features for a specific student."""
        metrics: StudentPerformanceMetrics | None = (
            StudentPerformanceMetrics.objects.filter(student=student).first()
        )

        if not metrics:
            return None

        features: dict[str, float] = {
            "attendance_rate": float(metrics.attendance_rate),
            "assignment_completion_rate": float(metrics.assignment_completion_rate),
            "average_assignment_score": float(metrics.average_assignment_score),
            "mid_term_grade": float(metrics.mid_term_grade or 0),
            "submission_timeliness": 0.0,
            "consistency_score": 0.0,
        }

        return features

    def predict_subject_grade(self, student: Student, subject: Subject) -> float | None:
        """Predict grade for a specific subject."""
        if subject.id not in self.subject_models:
            return None

        features: dict[str, float] | None = self.prepare_student_features(student)
        if not features:
            return None

        features_array: np.ndarray = np.array([list(features.values())])

        prediction: float = self.subject_models[subject.id].predict(
            self.scaler.transform(features_array)
        )[0]

        return round(prediction, 2)

    def predict_overall_grade(self, student: Student) -> float | None:
        """Predict overall board exam grade."""
        features: dict[str, float] | None = self.prepare_student_features(student)
        if not features:
            return None

        features_array: np.ndarray = np.array([list(features.values())])

        prediction: float = self.overall_model.predict(
            self.scaler.transform(features_array)
        )[0]

        return round(prediction, 2)

    def get_performance_factors(
        self, student: Student, subject: Subject | None = None
    ) -> dict[str, list[dict[str, str]]] | None:
        """
        Analyze and explain the factors affecting a student's predicted performance.
        Returns a dictionary of factors and their impact levels.
        """
        metrics: Any = StudentPerformanceMetrics.objects.filter(student=student)
        if subject:
            metrics = metrics.filter(subject=subject)

        metrics = metrics.first()
        if not metrics:
            return None

        factors: dict[str, list[dict[str, str]]] = {
            "Strong Points": [],
            "Areas for Improvement": [],
            "Neutral Factors": [],
        }

        if metrics.attendance_rate >= 90:
            factors["Strong Points"].append(
                {
                    "factor": "Attendance",
                    "description": f"Excellent attendance rate of {metrics.attendance_rate}%",
                }
            )
        elif metrics.attendance_rate < 75:
            factors["Areas for Improvement"].append(
                {
                    "factor": "Attendance",
                    "description": f"Attendance rate of {metrics.attendance_rate}%"
                    "needs improvement",
                    "suggestion": "Try to maintain at least 80% attendance for better academic"
                    "performance",
                }
            )
        else:
            factors["Neutral Factors"].append(
                {
                    "factor": "Attendance",
                    "description": f"Average attendance rate of {metrics.attendance_rate}%",
                }
            )

        if metrics.assignment_completion_rate >= 90:
            factors["Strong Points"].append(
                {
                    "factor": "Assignment Completion",
                    "description": "Excellent assignment completion rate of {}%".format(
                        metrics.assignment_completion_rate
                    ),
                }
            )
        elif metrics.assignment_completion_rate < 60:
            factors["Areas for Improvement"].append(
                {
                    "factor": "Assignment Completion",
                    "description": "Assignment completion rate of {}% needs attention".format(
                        metrics.assignment_completion_rate
                    ),
                    "suggestion": "Try to complete all assignments on time",
                }
            )

        if metrics.average_assignment_score >= 85:
            factors["Strong Points"].append(
                {
                    "factor": "Assignment Scores",
                    "description": "Strong average assignment score of {}%".format(
                        metrics.average_assignment_score
                    ),
                }
            )
        elif metrics.average_assignment_score < 70:
            factors["Areas for Improvement"].append(
                {
                    "factor": "Assignment Scores",
                    "description": "Average assignment score of {}% needs improvement".format(
                        metrics.average_assignment_score
                    ),
                    "suggestion": "Consider seeking additional help or tutoring",
                }
            )

        return factors

    def get_prediction_explanation(
        self, prediction: float, student: Student, subject: Subject | None = None
    ) -> dict[str, Any]:
        """
        Generate a human-readable explanation for the prediction.
        """
        factors: dict[str, list[dict[str, str]]] | None = self.get_performance_factors(
            student, subject
        )
        if not factors:
            return {"error": "Insufficient data to generate explanation"}

        explanation: dict[str, Any] = {
            "prediction": prediction,
            "confidence_level": self._get_confidence_level(factors),
            "factors": factors,
            "summary": self._generate_summary(prediction, factors),
            "recommendations": self._generate_recommendations(factors),
        }

        return explanation

    def _get_confidence_level(self, factors: dict[str, list[dict[str, str]]]) -> str:
        """
        Calculate confidence level based on available factors.
        """
        strong_points: int = len(factors["Strong Points"])
        areas_for_improvement: int = len(factors["Areas for Improvement"])
        neutral_factors: int = len(factors["Neutral Factors"])

        total_factors: int = strong_points + areas_for_improvement + neutral_factors

        if total_factors >= 5 and strong_points >= 2:
            return "High"
        elif total_factors >= 3:
            return "Medium"
        else:
            return "Low"

    def _generate_summary(
        self, prediction: float, factors: dict[str, list[dict[str, str]]]
    ) -> str:
        """
        Generate a summary of the prediction and key factors.
        """
        strength_count: int = len(factors["Strong Points"])
        improvement_count: int = len(factors["Areas for Improvement"])

        if prediction >= 85:
            base_summary = (
                "Excellent performance predicted based on strong academic indicators."
            )
        elif prediction >= 70:
            base_summary = (
                "Satisfactory performance predicted with room for improvement."
            )
        else:
            base_summary = """Performance prediction indicates need for additional
            support and improvement."""

        if strength_count > improvement_count:
            detail = f" Student shows strength in {strength_count} key areas."
        elif improvement_count > strength_count:
            detail = f" Focus needed in {improvement_count} areas for improvement."
        else:
            detail = " Performance shows a mix of strengths and areas for improvement."

        return base_summary + detail

    def _generate_recommendations(
        self, factors: dict[str, list[dict[str, str]]]
    ) -> list[str]:
        """
        Generate specific recommendations based on factors.
        """
        recommendations: list[str] = []

        for area in factors["Areas for Improvement"]:
            if "suggestion" in area:
                recommendations.append(area["suggestion"])

        if not recommendations:
            if factors["Strong Points"]:
                recommendations.append(
                    "Maintain current performance level and consider taking on additional"
                    "challenges"
                )
            else:
                recommendations.append(
                    "Focus on building consistent study habits and seek regular feedback"
                )

        return recommendations

    def predict_with_confidence_and_explanation(
        self, student: Student
    ) -> dict[str, Any]:
        """
        Predict grades with confidence intervals and detailed explanations.
        """
        predictions: dict[str, Any] = {}

        overall_grade: float | None = self.predict_overall_grade(student)
        if overall_grade is not None:
            explanation: dict[str, Any] = self.get_prediction_explanation(
                overall_grade, student
            )
            predictions["overall"] = {
                "predicted_grade": overall_grade,
                "confidence_range": (overall_grade - 5, overall_grade + 5),
                "explanation": explanation,
            }

        for subject in Subject.objects.filter(semester=student.semester):
            subject_grade: float | None = self.predict_subject_grade(student, subject)
            if subject_grade:
                subject_explanation: dict[str, Any] = self.get_prediction_explanation(
                    subject_grade, student, subject
                )
                predictions[subject.name] = {
                    "predicted_grade": subject_grade,
                    "confidence_range": (subject_grade - 3, subject_grade + 3),
                    "explanation": subject_explanation,
                }

        return predictions


def get_student_predictions_with_explanation(student_id: int) -> dict[str, Any]:
    """
    Get detailed predictions with explanations for a specific student.
    """

    try:
        user: User = User.objects.get(id=student_id)
        student: Student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        return {
            "error": "Student not found",
            "details": f"No student found with ID {student_id}",
        }

    predictor: GradePredictionSystem = GradePredictionSystem()
    predictor.train_models()

    predictions: dict[str, Any] = predictor.predict_with_confidence_and_explanation(
        student
    )

    if "overall" in predictions:
        predictions["summary"] = {
            "performance_trend": _get_performance_trend(predictions),
            "key_recommendations": _consolidate_recommendations(predictions),
            "confidence_summary": _get_confidence_summary(predictions),
        }

    return predictions


def _get_performance_trend(predictions: dict[str, Any]) -> str:
    """
    Analyze the overall performance trend across subjects.
    """
    grades: list[float] = [
        pred["predicted_grade"] for key, pred in predictions.items() if key != "summary"
    ]
    if not grades:
        return "Insufficient data"

    avg_grade: float = sum(grades) / len(grades)
    if avg_grade >= 85:
        return "Excellent performance across subjects"
    elif avg_grade >= 70:
        return "Satisfactory performance with room for improvement"
    else:
        return "Performance needs significant improvement"


def _consolidate_recommendations(predictions: dict[str, Any]) -> list[str]:
    """
    Consolidate and prioritize recommendations across all subjects.
    """
    all_recommendations: list[str] = []
    for pred in predictions.values():
        if isinstance(pred, dict) and "explanation" in pred:
            all_recommendations.extend(pred["explanation"].get("recommendations", []))

    return list(dict.fromkeys(all_recommendations))


def _get_confidence_summary(predictions: dict[str, Any]) -> str:
    """
    Summarize the confidence levels across predictions.
    """
    confidence_levels: list[str] = [
        pred["explanation"]["confidence_level"]
        for pred in predictions.values()
        if isinstance(pred, dict) and "explanation" in pred
    ]

    if not confidence_levels:
        return "Unable to determine confidence level"

    high_count: int = confidence_levels.count("High")
    medium_count: int = confidence_levels.count("Medium")
    low_count: int = confidence_levels.count("Low")

    if high_count > medium_count and high_count > low_count:
        return "High confidence in most predictions"
    elif medium_count > low_count:
        return "Moderate confidence in predictions"
    else:
        return "Limited confidence due to data constraints"
