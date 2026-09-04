# tools

## These scripts pull all data from SleepNumber Cloud site. This is enough information to know about you sexual activity

Standalone utilities that use the vendored `sleepiq_local` library directly, no
Home Assistant required. Credentials come from the environment; nothing is written
to disk.

```bash
SIQ_EMAIL='you@example.com' SIQ_PASS='your-password' python tools/inspect_bed.py
```

## `inspect_bed.py`

Logs in via Cognito and prints, for every sleeper:

- live presence, sleep number, and raw pressure
- with `--biometrics`, last night's SleepIQ score, average heart rate, respiration,
  HRV, and duration (biometric data is not fetched or printed unless asked for)

Useful for confirming the cloud path works for your account, and for capturing a
baseline of what data is still flowing before the cloud degrades further.

# Privacy Laws and Data Deletion Requests for Smart Devices

![Alt Text](https://images.contentstack.io/v3/assets/bltd4dd5b2d705252bc/blt6100b1a7b206d70b/6904ec23529fa0fce95b875f/us_state_laws_report_2025_map_graphic_mobile.png)

# US State Privacy Law & Enforcement Matrix

As the legal landscape surrounding consumer data protection evolves, businesses and consumers must navigate a patchwork of state-level privacy laws. The following matrix details key state privacy laws, their focus, and the regulatory bodies responsible for enforcing them.

## State Privacy Laws and Health Data Protections

| State | Privacy Law | Law Type | Enforcement Authority | Private Right of Action |
| :--- | :--- | :--- | :--- | :--- |
| **California** | California Consumer Privacy Act (CCPA) / CPRA | Comprehensive | Attorney General & California Privacy Protection Agency (CPPA) | Yes (Limited to data breaches) |
| **Washington** | My Health My Data Act (MHMDA) | Health Data Specific | Attorney General | Yes (Requires proving actual damages) |
| **Texas** | Texas Data Privacy and Security Act (TDPSA) | Comprehensive | Attorney General | No |
| **Nevada** | Consumer Health Data Privacy Law (SB 370) | Health Data Specific | Attorney General | No |
| **Connecticut**| Connecticut Data Protection Act (CTDPA) | Comprehensive (Includes Health Data Amendments) | Attorney General | No |
| **Virginia** | Virginia Consumer Data Protection Act (VCDPA) | Comprehensive | Attorney General | No |
| **Colorado** | Colorado Privacy Act (CPA) | Comprehensive | Attorney General & District Attorneys | No |
| **Utah** | Utah Consumer Privacy Act (UCPA) | Comprehensive | Attorney General | No |

### Key Definitions

* **Comprehensive Data Privacy Laws:** These laws apply across industries and grant rights to individuals pertaining to the collection, use, and disclosure of their personal data by businesses. 
* **Health Data Specific Laws:** These laws have exceptionally broad definitions intended to protect consumer health data, such as biometric information, outside of traditional healthcare settings. 
* **Private Right of Action:** This represents a provision allowing consumers to bring private lawsuits directly against companies. In most states, enforcement is strictly limited to the State Attorney General.

This document outlines how state privacy laws apply to smart devices like Sleep Number beds, which track sensitive health and biometric data, and provides a guide on how to submit a formal data deletion request.

## Smart Beds and Sensitive Data
Smart beds track metrics like heart rate, breathing, time in bed, and motion. Because these metrics can infer intimate activities, privacy policies explicitly acknowledge that this information may be considered "sensitive data" or "consumer health data" under certain state laws.

## States with Applicable Privacy Laws
There is no single federal data privacy law in the United States, but many states have stepped in to protect consumers.

* **Targeted Consumer Health Data Laws:** States like Washington, Nevada, and Connecticut have aggressive laws specifically guarding health and intimate data outside the traditional healthcare system. Washington's My Health My Data Act (MHMDA), for example, explicitly protects biometric data and "reproductive or sexual health information".
* **Comprehensive Data Privacy Laws:** More than 15 states have enacted broader privacy frameworks. These laws generally require companies to obtain affirmative consent before collecting or processing sensitive personal data.

## Who to Notify About Breaches or Violations
If a company retains sensitive data without your consent, fails to honor a deletion request, or exposes your data in a security breach, the enforcement authority depends on your state of residence:

* **State Attorneys General:** In almost every state with a privacy law, the State Attorney General is the primary regulatory enforcer. In Texas, for example, citizens can file privacy complaints directly through the Texas Attorney General's Consumer Complaint Portal.
* **Dedicated Privacy Agencies:** California is unique in that it established a dedicated agency-the California Privacy Protection Agency (CPPA)-to enforce the state's privacy act alongside the Attorney General.
* **Private Right of Action (Direct Lawsuits):** In most states, only the government can penalize a company for privacy violations. However, Washington's MHMDA allows consumers to sue companies directly for health data violations. California also allows individuals to file private lawsuits, but specifically in the event of a data breach.

> **Immediate Action for Sleep Number Owners:** You can stop the transmission of new sleep metrics to their cloud by enabling "Privacy Mode" in the Sleep Number app. To delete the historical data they already have, you must submit a verifiable deletion request or contact their customer service at 1-800-554-0184.

---

## How to Draft and Submit a Formal Data Deletion Request

Drafting a data deletion request requires being direct, citing the specific law that protects you, and submitting it through the company's designated legal channels. Your request will be governed by laws such as the **Texas Data Privacy and Security Act (TDPSA)**, which gives you the legal right to demand the deletion of personal data collected about you.

Here is how to execute a formal deletion request, using Sleep Number as the example:

### 1. Locate the Official Privacy Channel
Avoid standard customer service lines. Companies must provide a designated method for privacy requests. For Sleep Number, use their specific online Privacy Form or email their compliance team directly at **privacy@sleepnumber.com**.

### 2. Draft the Formal Request
Your letter doesn't need to be lengthy, but it must clearly state:
* Your state residency.
* The specific law you are invoking (e.g., TDPSA).
* A clear demand to delete all personal data, including data obtained from third parties.
* The email or phone number associated with your account so they can locate your profile.

### 3. Complete Identity Verification
To prevent malicious actors from deleting your account, companies are legally required to verify your identity. Sleep Number will likely reply asking you to confirm via a link sent to your account email, or by asking for purchase details. Do not ignore this follow-up, or the request will be dismissed.

### 4. Track the 45-Day Legal Window
Under the TDPSA and most other state privacy laws, a company has exactly **45 days** to comply with your deletion request once your identity is verified. They can take a one-time 45-day extension, but they must notify you of the delay within the initial window.

> **Key insight:** Companies are permitted to retain specific fragments of data even after a deletion request if it is legally required or necessary to fulfill an ongoing contract (like keeping your purchase record active to honor a bed warranty). However, behavioral and biometric tracking data, such as SleepIQ metrics, must be purged.
