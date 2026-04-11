from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CaseData:
    code_name: str
    title: str
    menu_blurb: str
    story_lines: tuple[str, ...]
    terminal_tips: tuple[str, ...]
    evidence_files: dict[str, tuple[str, ...]]
    puzzle_steps: tuple[PuzzleStep, ...]
    completion_lines: tuple[str, ...]

@dataclass(frozen=True)
class PuzzleStep:
    prompt: str
    answer: str
    success_message: str
    acceptable: tuple[str, ...] = ()

GAME_TITLE = "CyberCases: Cipher High"
GAME_SUBTITLE = "A story-driven mini CTF game set in a high school, about defending a school network."
WINDOW_SIZE = (1280, 720)
FPS = 60

MENU_INTRO = (
    "You are a student at Cipher High, and are part of its Cyber Defense Club.",
    "Each case mixes evidence analysis, beginner-friendly CTF decoding, and incident response.",
    "Use the terminal to inspect files, decode clues, and submit the best containment strategy for each case.",
)

GLOBAL_TERMINAL_TIPS = (
    "Left/Right/Home/End to move the cursor inside the prompt.",
    "Up/Down to cycle through previous commands.",
    "Press icon at top right to toggle fullscreen."
)

CASES = (
    CaseData(
        code_name= "CASE 01 // INBOX",
        title = "Phishing Invoice",
        menu_blurb = "base64, email headers, phising response",
        story_lines= (
            "A fake district IT message reached a faculty member's inbox before first period.",
            "Your history teacher, Mr. K, almost  opened an invoice attachment from a suspicious sender,",
             "but luckily asked the club for help first.",
            "Your job is to decode the attachment token, and find the phising domain,",
            "and recommend the best containment strategy.",
        ),
        terminal_tips= (
            "Use decode on the attachment token in the email evidence.",
            "Compare the sender address against the real school domain in the headers.",
            "Containment questions want the best immediate response, not every response.",
        ),
        evidence_files= {
            "briefing.txt": (
                "Briefing:",
                "- Attack started at 08:03 AM.",
                "- One teacher nearly opened a fake invoice attachment.",
                "- The terminal can decode base64 strings from the email.",
                "- Submit the payload name first, then the sender domain, then the best reponse."
            ),
            "email.txt": (
                "From: District IT Support <security-update@school-it-helpdesk.com>",
                "To: Faculty Staff",
                "Subject: Urgent invoice review needed",
                "",
                "Please review the updated invoice package before noon.",
                "Attachment token: aW52b2ljZS56aXA=",
                "",
                "If you cannot open it, reply with your school password for manual verification."
            ),
            "headers.log": (
                "Received: mailer.school-it-helpdesk.com (185.14.82.44)",
                "Return-Path: bounce@school-it-helpdesk.com",
                "SPF: fail",
                "DKIM: none",
                "Note: Official district email should end in cipherhigh.edu"
            ),
            "club_chat.txt": (
                "Mina: thr sender looks fake spf failed ",
                "Yukino: if anyone opened it reset pwds and block the domain asap",
                "Mr. F: Can we not be texting before school starts? You're giving me too many notifications. Also use full words.",
                "Yukino: ok fine. reset passwords and block the domain immediately. "
            )
        }, 
        puzzle_steps = (
            PuzzleStep(
                prompt = "Step 1: Identify the attachment payload name.",
                answer = "invoice.zip",
                success_message= "Payload confirmed."
            ),
            PuzzleStep(
                prompt = "Step 2: Find the name of the phishing sender domain to block.",
                answer = "school-it-helpdesk.com",
                success_message = "Domain confirmed.",
            ),
            PuzzleStep(
                prompt = "Step 3: What is the best immediate response?",
                answer = "reset pwds",
                success_message= "Containment approved.",
                acceptable = (
                    "reset passwords",
                    "password reset",
                    "reset teacher passwords",
                    "reset staff passwords",
                    "reset compromised passwords", 
                    "reset pwd"
                )
            )
        ),
        completion_lines = (
            "You shut down the phishing wave before any creditials were collected.",
            "The club has all the required details and a clear response.",
            "CASE 01 completed!"
        )
    ), 
    CaseData(
        code_name = "CASE 02 // LAB MYSTERY", 
        title = "Rogue USB",
        menu_blurb = "hex decoding, endpoint logs, workstation containment",
        story_lines = (
            "A USB drive labeled FINAL EXAM ANSWERS was found outside of the computer lab.",
            "Someone plugged it into a worksation in the library, and the endpoint monitor lit up."
            "Trace the launched payload, identify the autorun file that trigered it,",
            "and recommend the best immdeiate action before the malware spreads."
        ),
        terminal_tips = (
            "The suspicious token in the breifing is hex, not base64.",
            "Check the endpoint log for the file that autoran.",
            "For a live workstation incident, think containment first."
        ),
        evidence_files = {
            "briefing.txt": (
                "Briefing:",
                "- Student monitor reported a flash drive plugged into LIB-04.",
                "- Binary token recovered from the launch command: 706179726f6c6c2e657865",
                "- One suspicious process spawned before the drive was removed.",
                "- Submit the launched executable, then the autorun file, then the best response."
            ),
            "endpoint.log": (
                "08:42:11 DeviceMount F:\\label=FINAL_EXAM_ANSWERS",
                "08:42:13 FileRead E:\\autorun.inf",
                "08:42:13 ProcessStart parent=explorer.exe image=E:\\payroll.exe",
                "08:42:18 NetConnect process=payroll.exe dst=91.240.118.12:443"
            ),
            "hallway_report.txt": (
                "Reporter note:",
                "- USB casing was black with a handwritten label on it."
                "- Nobody recongnized the drive as school propery.",
                "- A teacher unplugged it after the suspicious pop-up appeared."
            ),
            "club_chat.txt": (
                "Priya: that usb drive's name is highkey tempting.",
                "Ms. M: yeah, that's why it's called social engineering.",
                "Ryan: if the machine already launched it, isolate the workstation first.",
                "Ms. M: we can image it later, rn stop lateral movement."
            )
        },
        puzzle_steps = (
            PuzzleStep(
                prompt = "Step 1: Identify the executable launched from the USB.",
                answer = "payroll.exe",
                success_message = "Payload identified. This was the real trap."
            ),
            PuzzleStep(
                prompt = "Step 2: name the file that triggered the automatic launch.",
                answer = "autorun.inf",
                success_message = "Trigger file confirmed."
            ),
            PuzzleStep(
                prompt = "Step 3: What is the best immediate response?",
                answer = "isolate workstation",
                success_message = "Containment approved.",
                acceptable = (
                    "isolate the workstation",
                    "isolate machine"
                    "isolate the machine",
                    "disconnect workstation",
                    "disconnect the workstation",
                    "isolate pc",
                    "isolate the pc",
                    "isolate PC",
                    "isolate the PC"
                )
            )
        ),
        completion_lines = (
            "You traced the USB payload and contained the infected workstation.",
            "The team can now invetigaste safely without leaving the host online.",
            "CASE 02 completed!"
        )
    ),
    CaseData(
        code_name = "CASE 03 // PORTAL PHANTOM",
        title = "Rogue Login Portal",
        menu_blurb = "ROT13 clue, auth logs, and account hardening",
        story_lines = (
            "A fake login page appeared on a student laptop after lunch.",
            "The attacker cloned the school portal and began collecting passwords from students.",
            "Decode the hidden domain clue, identify the attacking IP from the auth feed,",
            "and choose the best hardening step to protect affected accounts."
        ),
        terminal_tips= (
            "Use rot13 on the sticky note clue recovered near the kiosk.",
            "The auth feed shows the source that kept hammering the login portal.",
        ),
        evidence_files= {
            "briefing.txt": (
                "Briefing:",
                "- A cloned portal targeted students using school laptops.",
                "- Sticky note clue was recovered near the checkout kiosk: pvcureuvtu-ybtva.arg",
                "- You need to find the fake domain, attacker IP, and best hardening step."
            ),
            "portal_capture.html": (
                "<form action='https://cipherhigh-login.net/verify'>",
                "  <input name='student_id'>",
                "  <input name='password' type='password'>",
                "</form>",
                "<!-- cloned from the real district portal -->",
            ),
            "auth_feed.log": (
                "12:16:04 FAIL student.portal 45.77.19.24 user=nhs.treasurer",
                "12:16:11 FAIL student.portal 45.77.19.24 user=club.secretary",
                "12:16:20 FAIL student.portal 45.77.19.24 user=robotics.lead",
                "12:16:38 MFA_CHALLENGE_DISABLED legacy-account",
            ),
            "club_chat.txt": (
                "Alex: the cloned domain is close enough to trick tired people",
                "Emma: we should block the host and enable mutli factor authentication (MFA) for exposed accounts",
                "Mrs. R: This is why we need to verify links before we type passwords."
            ),
        },
        puzzle_steps = (
            PuzzleStep(
                prompt= "Step 1: Decode the fake portal domain from the sticky note clue.",
                answer = "cipherhigh-login.net",
                success_message= "Domain decoded."
            ),
            PuzzleStep(
                prompt="Step 2: Find the source IP that was hammering the login portal.",
                answer="45.77.19.24",
                success_message="Attacking IP confirmed."
            ),
            PuzzleStep(
                prompt="Step 3: What is the best hardening step?",
                answer="enable mfa",
                success_message="Hardening approved.",
                acceptable=(
                    "enable multi factor authentication",
                    "turn on mfa",
                    "turn on multi factor authentication",
                    "mfa",
                    "multi factor authentication"
                )
            )
        ),
        completion_lines=(
            "You found the fake portal, traced the attacker traffic, and locked accounts.",
            "Students can keep working without giving out credentials to clones.",
            "CASE 03 completed!" 
        )
    )
)
