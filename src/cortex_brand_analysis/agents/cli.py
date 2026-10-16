from __future__ import annotations

from cortex_brand_analysis.agents.pria import PriaAgent
from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.domain.agent import PriaRequest


def main() -> None:
    agent = PriaAgent(get_settings())
    previous_response_id: str | None = None

    print("PRIA v2 iniciada. Digite 'q' para sair.")

    while True:
        message = input("\nVocê: ").strip()
        if message.lower() == "q":
            break
        if not message:
            continue

        result = agent.run(
            PriaRequest(
                message=message,
                previous_response_id=previous_response_id,
            )
        )
        previous_response_id = result.response_id
        print(f"\nPRIA: {result.answer}")


if __name__ == "__main__":
    main()
