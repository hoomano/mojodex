import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const token: any = await getToken({ req, secret: process.env.NEXT_AUTH_JWT_SECRET });

  let OnboardingRedirectionWhiteList = [
    "/onboarding",
    "/auth/authorize",
    "/auth/mobile",
    "/payment",
    "/payment/mobile",
  ];

  // /auth/authorize and /auth/mobile new conditions allow to bypass the redirection to /onboarding used by the mobile app
  if (
    token &&
    token.authorization &&
    !token.authorization.onboarding_presented &&
    !OnboardingRedirectionWhiteList.includes(path)
  ) {
    return NextResponse.redirect(new URL("/onboarding", req.url));
  } else if (path === "/") {
    return NextResponse.redirect(new URL("/tasks", req.url));
  } else {
    return NextResponse.next();
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|images|Build|mojo-perception.min.js).*)",
  ],
};
