from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

from academics.models import AssignmentSubmission, Subject
from EduTrack.utils import get_or_not_found
from evaluations.models import StudentPerformanceMetrics
from users.models import Student, User


class SubjectScorePrediction:
    def __init__(self) -> None:
        self.subject_models: dict[Any, Any] = {}
        self.scaler: StandardScaler = StandardScaler()

    def analyze_subject_performance(
        self, student: Student, subject: Subject
    ) -> dict[str, Any] | None:
        """Analyze student's performance in a specific subject"""
        try:
            metrics: StudentPerformanceMetrics = StudentPerformanceMetrics.objects.get(
                student=student, subject=subject
            )

            submissions: Any = AssignmentSubmission.objects.filter(
                student=student, assignment__subject=subject
            ).select_related("assignment")

            topic_performance: dict[
                Subject, dict[str, Any]
            ] = self._calculate_topic_performance(submissions)

            strengths, weaknesses = self._identify_strength_weakness(
                topic_performance, metrics.average_assignment_score
            )

            analysis: dict[str, Any] = {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "current_average": float(metrics.average_assignment_score),
                "attendance_impact": self._analyze_attendance_impact(
                    metrics.attendance_rate
                ),
                "assignment_completion": float(metrics.assignment_completion_rate),
                "topic_wise_performance": {
                    subject.name: topic_performance[subject]
                    if subject in topic_performance
                    else {}
                },
                "strengths": strengths,
                "weaknesses": weaknesses,
                "improvement_potential": self._calculate_improvement_potential(metrics),
                "predicted_score_range": self._predict_score_range(metrics),
                "confidence_level": self._calculate_confidence_level(
                    metrics, submissions.count()
                ),
            }

            return analysis

        except StudentPerformanceMetrics.DoesNotExist:
            return None

    def _calculate_topic_performance(
        self, submissions: Any
    ) -> dict[Subject, dict[str, Any]]:
        """Calculate performance in different topics within the subject"""
        topic_scores: dict[Subject, list[float]] = {}

        for submission in submissions:
            if not submission.score:
                continue
            topic: Subject = submission.assignment.subject
            score: float = float(submission.score)
            max_score: float = float(submission.assignment.max_score)
            percentage: float = (score / max_score) * 100

            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(percentage)

        return {
            topic: {
                "average": np.mean(scores),
                "trend": self._calculate_trend(scores),
                "submissions": len(scores),
            }
            for topic, scores in topic_scores.items()
        }

    def _calculate_trend(self, scores: list[float]) -> str:
        """Calculate performance trend (improving, declining, stable)"""
        if len(scores) < 2:
            return "Insufficient data"

        slope: float = np.polyfit(range(len(scores)), scores, 1)[0]

        if slope > 2:
            return "Improving"
        elif slope < -2:
            return "Declining"
        else:
            return "Stable"

    def _identify_strength_weakness(
        self,
        topic_performance: dict[Subject, dict[str, Any]],
        overall_average: float | str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Identify strong and weak topics"""
        strengths: list[dict[str, Any]] = []
        weaknesses: list[dict[str, Any]] = []
        overall_average_float: float = float(overall_average)

        for topic, data in topic_performance.items():
            avg: float = data["average"]
            if avg >= overall_average_float + 5:
                strengths.append({"topic": topic, "score": avg, "trend": data["trend"]})
            elif avg <= overall_average_float - 5:
                weaknesses.append(
                    {"topic": topic, "score": avg, "trend": data["trend"]}
                )

        return strengths, weaknesses

    def _analyze_attendance_impact(
        self, attendance_rate: float | str
    ) -> dict[str, float | str]:
        """Analyze impact of attendance on performance"""
        attendance_rate_float: float = float(attendance_rate)

        if attendance_rate_float >= 90:
            impact: str = "Positive"
            description: str = "High attendance rate contributing to better performance"
        elif attendance_rate_float >= 75:
            impact = "Neutral"
            description = "Moderate attendance may affect consistency"
        else:
            impact = "Negative"
            description = "Low attendance likely affecting performance"

        return {
            "rate": attendance_rate_float,
            "impact": impact,
            "description": description,
        }

    def _calculate_improvement_potential(
        self, metrics: StudentPerformanceMetrics
    ) -> dict[str, Any]:
        """Calculate potential for improvement"""
        current_average: float = float(metrics.average_assignment_score)
        completion_rate: float = float(metrics.assignment_completion_rate)

        completion_improvement: float = (100 - completion_rate) * 0.2

        score_improvement: float = (100 - current_average) * 0.3

        total_potential: float = min(completion_improvement + score_improvement, 20)

        return {
            "potential_improvement": round(total_potential, 1),
            "factors": {
                "completion_impact": round(completion_improvement, 1),
                "current_performance_impact": round(score_improvement, 1),
            },
            "recommendations": self._generate_improvement_recommendations(metrics),
        }

    def _predict_score_range(
        self, metrics: StudentPerformanceMetrics
    ) -> dict[str, Any]:
        """Predict expected score range for final exam"""
        current_average: float = float(metrics.average_assignment_score)
        completion_rate: float = float(metrics.assignment_completion_rate)
        attendance_rate: float = float(metrics.attendance_rate)

        base_prediction: float = current_average

        completion_adjustment: float = (completion_rate - 80) * 0.1

        attendance_adjustment: float = (attendance_rate - 80) * 0.1

        final_prediction: float = (
            base_prediction + completion_adjustment + attendance_adjustment
        )

        lower_bound: float = max(0, final_prediction - 5)
        upper_bound: float = min(100, final_prediction + 5)

        return {
            "predicted_score": round(final_prediction, 1),
            "range": {"lower": round(lower_bound, 1), "upper": round(upper_bound, 1)},
            "factors_considered": {
                "current_average": current_average,
                "completion_impact": round(completion_adjustment, 1),
                "attendance_impact": round(attendance_adjustment, 1),
            },
        }

    def _calculate_confidence_level(
        self, metrics: StudentPerformanceMetrics, submission_count: int
    ) -> dict[str, Any]:
        """Calculate confidence level of prediction"""
        factors: list[tuple[str, str]] = []

        if submission_count >= 10:
            factors.append(("High", "Sufficient number of assignments"))
        elif submission_count >= 5:
            factors.append(("Medium", "Moderate number of assignments"))
        else:
            factors.append(("Low", "Limited assignment data"))

        if float(metrics.attendance_rate) >= 85:
            factors.append(("High", "Consistent attendance"))
        elif float(metrics.attendance_rate) >= 70:
            factors.append(("Medium", "Moderate attendance"))
        else:
            factors.append(("Low", "Poor attendance"))

        if float(metrics.assignment_completion_rate) >= 85:
            factors.append(("High", "High assignment completion"))
        elif float(metrics.assignment_completion_rate) >= 70:
            factors.append(("Medium", "Moderate assignment completion"))
        else:
            factors.append(("Low", "Low assignment completion"))

        confidence_levels: list[str] = [level for level, _ in factors]
        if confidence_levels.count("High") >= 2:
            overall: str = "High"
        elif confidence_levels.count("Low") >= 2:
            overall = "Low"
        else:
            overall = "Medium"

        return {
            "level": overall,
            "factors": [
                {"level": level, "reason": reason} for level, reason in factors
            ],
        }

    def _generate_improvement_recommendations(
        self, metrics: StudentPerformanceMetrics
    ) -> list[dict[str, str]]:
        """Generate specific recommendations for improvement"""
        recommendations: list[dict[str, str]] = []

        if float(metrics.attendance_rate) < 85:
            recommendations.append(
                {
                    "area": "Attendance",
                    "recommendation": "Improve class attendance to at least 85%",
                    "impact": "High",
                }
            )

        if float(metrics.assignment_completion_rate) < 90:
            recommendations.append(
                {
                    "area": "Assignment Completion",
                    "recommendation": "Complete all assignments on time",
                    "impact": "High",
                }
            )

        avg_score: float = float(metrics.average_assignment_score)
        if avg_score < 70:
            recommendations.append(
                {
                    "area": "Performance",
                    "recommendation": "Seek additional help through tutoring",
                    "impact": "High",
                }
            )
        elif avg_score < 85:
            recommendations.append(
                {
                    "area": "Performance",
                    "recommendation": "Focus on improving weak topics",
                    "impact": "Medium",
                }
            )

        return recommendations


def get_subject_predictions(
    student_id: int, subject_id: int | None = None
) -> dict[str, Any]:
    """Get detailed subject-wise predictions for a student"""
    try:
        user: User = get_or_not_found(User.objects.all(), pk=student_id)
        student: Student = Student.objects.get(user=user)
        predictor: SubjectScorePrediction = SubjectScorePrediction()

        if subject_id:
            subject: Subject = get_or_not_found(Subject.objects.all(), pk=subject_id)
            analysis: dict[str, Any] | None = predictor.analyze_subject_performance(
                student, subject
            )
            if analysis:
                return {subject.name: analysis}
            else:
                raise LookupError(
                    f"No data available of {user.get_full_name()} for the subject {subject.name}."
                )
        else:
            subjects: Any = Subject.objects.filter(semester=student.semester)
            predictions: dict[str, Any] = {}

            for subject in subjects:
                analysis: dict[str, Any] | None = predictor.analyze_subject_performance(
                    student, subject
                )
                if analysis:
                    predictions[subject.name] = analysis

            if not predictions:
                raise LookupError("No data available for any subjects in the semester.")

            return predictions

    except Student.DoesNotExist:
        return {"error": "Student not found"}
    except Subject.DoesNotExist:
        return {"error": "Subject not found"}
