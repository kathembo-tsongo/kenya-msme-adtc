import json

example = {"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I'm a Ugandan national running a small trading business in Kenya, but I don't have proper legal documentation. Where do I even start?"},
    {"role": "assistant", "content": "Here's where to start: go to the **Kenya eFNS portal** on eCitizen and apply for a **Class R Permit** \u2014 this is the special permit for East African Community nationals (Burundi, DR Congo, Rwanda, South Sudan, Tanzania, Uganda), and it covers residing, working, trading, or running a business in Kenya.\n\nThe permit itself is **free**: the processing fee is KES 0 and the issuance fee is KES 0, gazetted under the Kenya Citizenship and Immigration Amendment Regulations 2024. However, you will also need a separate **Foreigner Certificate (Alien Card)**, which costs **KES 5,000 per year**.\n\nFor documents, you'll typically need your valid passport, a cover letter explaining your business activity, your KRA PIN if you're doing business, and a police clearance certificate (required specifically for small-scale traders). Requirements can vary by situation, so confirm the exact list for your case on the eFNS portal.\n\nThe application starts online, but you'll need to print the completed forms and submit them physically at the Immigration offices (Nyayo House, Nairobi) to complete the process.\n\nAnd beyond the paperwork \u2014 you're not doing anything wrong by seeking to regularize your status. Kenya and its EAC neighbours share a Common Market specifically to make this kind of cross-border trade and residence possible."}
]}

with open("new_example_class_r.jsonl", "w", encoding="utf-8") as f:
    f.write(json.dumps(example, ensure_ascii=False) + "\n")

print("Wrote 1 new training example to new_example_class_r.jsonl")
