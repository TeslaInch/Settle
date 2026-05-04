"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { createAgreement } from "@/lib/api";
import {
  validateEmail,
  validateAmount,
  validateFutureDate,
  validateTerms,
  markFirstAgreementCreated,
} from "@/lib/utils";

interface FormState {
  title: string;
  amount: string;
  terms: string;
  counterparty_email: string;
  repayment_date: string;
}

interface FormErrors {
  title?: string;
  amount?: string;
  terms?: string;
  counterparty_email?: string;
  repayment_date?: string;
}

export default function NewAgreementPage() {
  const router = useRouter();

  const [form, setForm] = useState<FormState>({
    title: "",
    amount: "",
    terms: "",
    counterparty_email: "",
    repayment_date: "",
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const set = (field: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const validate = (): boolean => {
    const errs: FormErrors = {};

    if (!form.title.trim()) errs.title = "Title is required";
    const amountErr = validateAmount(form.amount);
    if (amountErr) errs.amount = amountErr;
    const termsErr = validateTerms(form.terms);
    if (termsErr) errs.terms = termsErr;
    const emailErr = validateEmail(form.counterparty_email);
    if (emailErr) errs.counterparty_email = emailErr;
    const dateErr = validateFutureDate(form.repayment_date);
    if (dateErr) errs.repayment_date = dateErr;

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validate()) return;

    setSubmitting(true);

    const res = await createAgreement({
      title: form.title.trim(),
      amount: parseFloat(form.amount),
      terms: form.terms.trim(),
      counterparty_email: form.counterparty_email.trim(),
      repayment_date: new Date(form.repayment_date).toISOString(),
    });

    setSubmitting(false);

    if (res.status === 0) {
      setApiError("Check your connection and try again.");
      return;
    }

    if (res.status === 401) {
      router.push("/login?reason=session_expired");
      return;
    }

    if (res.error) {
      setApiError(res.error);
      return;
    }

    markFirstAgreementCreated();
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      {/* Header */}
      <div className="bg-white px-4 pt-12 md:pt-6 pb-4 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} aria-label="Back">
            <ArrowLeft size={22} className="text-gray-700" />
          </button>
          <h1 className="font-semibold text-gray-900">New Agreement</h1>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate className="px-4 py-5 space-y-4">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Agreement title
          </label>
          <input
            type="text"
            value={form.title}
            onChange={set("title")}
            placeholder="e.g. Loan for rent"
            className={`w-full rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.title ? "border-red-400" : "border-gray-200"
            }`}
          />
          {errors.title && <p className="mt-1 text-xs text-red-500">{errors.title}</p>}
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Amount (₦)
          </label>
          <input
            type="number"
            inputMode="decimal"
            value={form.amount}
            onChange={set("amount")}
            placeholder="0.00"
            min="1"
            className={`w-full rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.amount ? "border-red-400" : "border-gray-200"
            }`}
          />
          {errors.amount && <p className="mt-1 text-xs text-red-500">{errors.amount}</p>}
        </div>

        {/* Counterparty email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Other party&apos;s email address
          </label>
          <input
            type="email"
            inputMode="email"
            autoComplete="off"
            value={form.counterparty_email}
            onChange={set("counterparty_email")}
            placeholder="them@example.com"
            className={`w-full rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.counterparty_email ? "border-red-400" : "border-gray-200"
            }`}
          />
          {errors.counterparty_email && (
            <p className="mt-1 text-xs text-red-500">{errors.counterparty_email}</p>
          )}
        </div>

        {/* Repayment date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Repayment date
          </label>
          <input
            type="date"
            value={form.repayment_date}
            onChange={set("repayment_date")}
            min={new Date().toISOString().split("T")[0]}
            className={`w-full rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.repayment_date ? "border-red-400" : "border-gray-200"
            }`}
          />
          {errors.repayment_date && (
            <p className="mt-1 text-xs text-red-500">{errors.repayment_date}</p>
          )}
        </div>

        {/* Terms */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Terms{" "}
            <span className="text-gray-400 font-normal">(min. 20 characters)</span>
          </label>
          <textarea
            value={form.terms}
            onChange={set("terms")}
            placeholder="Describe the agreement terms clearly…"
            rows={4}
            className={`w-full rounded-xl border px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 resize-none ${
              errors.terms ? "border-red-400" : "border-gray-200"
            }`}
          />
          <div className="flex justify-between mt-1">
            {errors.terms ? (
              <p className="text-xs text-red-500">{errors.terms}</p>
            ) : (
              <span />
            )}
            <p className="text-xs text-gray-400">{form.terms.length} chars</p>
          </div>
        </div>

        {apiError && (
          <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3">
            <p className="text-sm text-red-600">{apiError}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-2xl bg-green-600 py-3.5 text-sm font-semibold text-white disabled:opacity-60 active:scale-[0.98] transition-transform"
        >
          {submitting ? "Creating…" : "Create Agreement"}
        </button>
      </form>
    </div>
  );
}
