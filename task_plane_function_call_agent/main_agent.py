from logs.logger import logger
from agent.base_agent import TPFCAgent


def main():
    agent = TPFCAgent()
    while True:
        try:
            prompt = input("Enter your prompt (or 'exit'/'quit' to quit): ")
            # prompt = "帮我计算 4 * 6+2^ 5/ 3-1 ，并把结果写入到 clac.txt"
            # prompt = "写一个20字的自我介绍，保存下来"
            prompt_lower = prompt.lower()
            if prompt_lower in ["exit", "quit"]:
                logger.info("Goodbye!")
                break
            if not prompt.strip():
                logger.warning("Skipping empty prompt.")
                continue
            logger.warning("Processing your request...")
            agent.run(prompt)
        except KeyboardInterrupt:
            logger.warning("Goodbye!")
            break


if __name__ == "__main__":
    main()
