"""Prompt builder — constructs prompts for different LLM scenarios."""

from typing import Any, Dict, Optional


class PromptBuilder:
    """Builds structured prompts for different LLM use cases."""

    # Arabic ISP customer service prompt
    RAG_ANSWER_TEMPLATE = """أنت مساعد ذكي لشركة إنترنت هايبرنت ومركز خدمة عملاء.

أجب باللغة العربية فقط. اجعل إجابتك قصيرة ومباشرة.
اعتمد فقط على المعلومات الموجودة في السياق.
لا تشترط أن تكون كلمات السؤال مطابقة تماماً لكلمات السياق.
إذا كان المعنى موجوداً في السياق، أجب بناءً عليه.
إذا لم تجد معلومات كافية أو كانت ثقتك بالإجابة منخفضة، قل فقط:
  يرجى المتابعة مع الدعم الفني عبر واتساب: https://wa.me/967770000000

السياق:
{context}

السؤال:
{question}

الإجابة:"""

    CRM_SUMMARY_TEMPLATE = """أنت مساعد خدمة عملاء لشركة إنترنت.
قم بتلخيص المعلومات التالية من نظام CRM بشكل مفهوم للعميل.
أجب باللغة العربية فقط. اجعل التلخيص قصيراً ومباشراً.

نوع الطلب: {intent}
بيانات CRM:
{crm_data}

الرد المناسب للعميل:"""

    COMBINED_TEMPLATE = """أنت مساعد ذكي لشركة إنترنت.
أجب باللغة العربية فقط. اجعل إجابتك قصيرة ومباشرة.

نوع الطلب: {intent}

معلومات من قاعدة المعرفة:
{rag_context}

معلومات من نظام العملاء:
{crm_data}

سؤال العميل: {question}

قدم إجابة شاملة ومفيدة:"""

    GREETING_TEMPLATE = """أنت مساعد خدمة عملاء ودود لشركة إنترنت.
رد على تحية العميل بشكل لطيف ومهني وباختصار شديد.
اسأله كيف يمكنك مساعدته.

رسالة العميل: {message}

الرد:"""

    def build_rag_prompt(self, question: str, context: str) -> str:
        return self.RAG_ANSWER_TEMPLATE.format(context=context, question=question)

    def build_crm_prompt(self, intent: str, crm_data: str) -> str:
        return self.CRM_SUMMARY_TEMPLATE.format(intent=intent, crm_data=crm_data)

    def build_combined_prompt(self, question: str, intent: str,
                              rag_context: str, crm_data: str) -> str:
        return self.COMBINED_TEMPLATE.format(
            intent=intent, rag_context=rag_context,
            crm_data=crm_data, question=question,
        )

    def build_greeting_prompt(self, message: str) -> str:
        return self.GREETING_TEMPLATE.format(message=message)

