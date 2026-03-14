"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Formik, Form, Field, ErrorMessage } from "formik";
import * as Yup from "yup";
import { Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";

const registerSchema = Yup.object({
  companyName: Yup.string()
    .min(2, "Company name must be at least 2 characters")
    .required("Company name is required"),
  name: Yup.string()
    .min(2, "Name must be at least 2 characters")
    .required("Your name is required"),
  email: Yup.string().email("Invalid email address").required("Email is required"),
  password: Yup.string()
    .min(8, "Password must be at least 8 characters")
    .required("Password is required"),
});

export default function RegisterPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Branding */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
              <Wrench className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold">PlumbPro AI</span>
          </Link>
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-muted-foreground mt-1">
            Set up your company and start managing jobs with AI
          </p>
        </div>

        {/* Card */}
        <div className="bg-card rounded-xl border p-6 shadow-sm">
          <Formik
            initialValues={{
              companyName: "",
              name: "",
              email: "",
              password: "",
            }}
            validationSchema={registerSchema}
            onSubmit={async (values, { setSubmitting }) => {
              try {
                await apiFetch("/api/auth/register", {
                  method: "POST",
                  body: JSON.stringify({
                    company_name: values.companyName,
                    name: values.name,
                    email: values.email,
                    password: values.password,
                  }),
                });
                toast.success("Account created! Please sign in.");
                router.push("/login");
              } catch (err: unknown) {
                const message =
                  err instanceof Error ? err.message : "Registration failed";
                toast.error(message);
              } finally {
                setSubmitting(false);
              }
            }}
          >
            {({ isSubmitting }) => (
              <Form className="space-y-4">
                <div>
                  <label
                    htmlFor="companyName"
                    className="block text-sm font-medium mb-1.5"
                  >
                    Company Name
                  </label>
                  <Field
                    as={Input}
                    id="companyName"
                    name="companyName"
                    placeholder="Acme Plumbing Co."
                  />
                  <ErrorMessage
                    name="companyName"
                    component="p"
                    className="text-sm text-destructive mt-1"
                  />
                </div>

                <div>
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium mb-1.5"
                  >
                    Your Name
                  </label>
                  <Field
                    as={Input}
                    id="name"
                    name="name"
                    placeholder="John Smith"
                    autoComplete="name"
                  />
                  <ErrorMessage
                    name="name"
                    component="p"
                    className="text-sm text-destructive mt-1"
                  />
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium mb-1.5"
                  >
                    Email
                  </label>
                  <Field
                    as={Input}
                    id="email"
                    name="email"
                    type="email"
                    placeholder="john@acmeplumbing.com"
                    autoComplete="email"
                  />
                  <ErrorMessage
                    name="email"
                    component="p"
                    className="text-sm text-destructive mt-1"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium mb-1.5"
                  >
                    Password
                  </label>
                  <Field
                    as={Input}
                    id="password"
                    name="password"
                    type="password"
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                  />
                  <ErrorMessage
                    name="password"
                    component="p"
                    className="text-sm text-destructive mt-1"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Creating Account..." : "Create Account"}
                </Button>
              </Form>
            )}
          </Formik>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
