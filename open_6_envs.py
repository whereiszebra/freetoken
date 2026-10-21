import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "http://110.42.240.239/purchase/requisition"

# 6 个环境的名字，会作为 user_data_dir 的子目录名
ENV_NAMES = ["env_1", "env_2", "env_3", "env_4", "env_5", "env_6"]


async def open_env(p, name, index):
    # 每个环境一个独立的持久化上下文 = 独立浏览器进程 + 独立登录态
    context = await p.chromium.launch_persistent_context(
        user_data_dir=f"./browser_data/{name}",
        headless=False,
        viewport={"width": 1280, "height": 800},
        args=[
            f"--window-position={index * 160},{index * 80}",
            "--window-size=1280,800",
        ],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(TARGET_URL)
    print(f"[{name}] 已打开 → {TARGET_URL}")
    return context


async def main():
    async with async_playwright() as p:
        contexts = await asyncio.gather(
            *[open_env(p, name, i) for i, name in enumerate(ENV_NAMES)]
        )
        print("\n6 个环境已就绪，请手动登录和操作。")
        print("关闭所有浏览器窗口，或按 Ctrl+C 结束脚本。")
        # 一直挂着，直到你手动关掉或 Ctrl+C
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())