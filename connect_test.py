import asyncio
import random
from playwright.async_api import async_playwright
print("脚本开始执行...")
async def ask_deepseek(page, question, max_retries=3, timeout=120):
    for attempt in range(max_retries):
        try:
            input_box = page.locator('textarea[placeholder*="Message"], textarea[placeholder*="消息"], [contenteditable="true"]').first
            
            try:
                await input_box.wait_for(state="visible", timeout=5000)
            except Exception:
                print(f"\n❌ [第 {attempt+1} 次重试] 未找到输入框！等待 10 秒重试...\n")
                await asyncio.sleep(10)
                continue
            
            # 1. 清空输入框（防止有残留内容）
            await input_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 2. 使用 fill 瞬间填入内容（防掉字，且模拟粘贴动作）
            await input_box.fill(question)
            
            # 3. 发送前犹豫一下
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # 4. 发送动作（按 Enter 和 点击按钮双管齐下）
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5) # 稍等一下，看 Enter 是否生效
            
            # 检查输入框里是否还有文字（如果有，说明 Enter 没发出去）
            remaining_text = await input_box.inner_text()
            if remaining_text.strip(): 
                # 如果是 textarea，inner_text 可能拿不到，换用 input_value()
                try:
                    val = await input_box.input_value()
                    if val.strip():
                        # 按 Enter 失败，点击发送按钮
                        # 发送按钮通常是输入框右侧最后一个包含 svg 的 button
                        print("⚠️ Enter 未生效，尝试点击发送按钮...")
                        send_btn = page.locator("button").filter(has=page.locator("svg")).last
                        await send_btn.click()
                except:
                    pass
            
            print(f"🚀 已发送 (共 {len(question)} 字)，等待回复生成...")
            
            # ==========================================
            # 5. 随机化的轮询检测间隔
            # ==========================================
            answer_locator = page.locator(".ds-markdown").last
            
            last_text = ""
            stable_count = 0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                await asyncio.sleep(random.uniform(1.5, 3.5)) 
                
                try:
                    current_text = await answer_locator.inner_text(timeout=1000)
                except:
                    continue
                    
                if not current_text:
                    continue
                    
                # 确保抓到的不是上一个问题的旧回答
                if "扮演" in current_text and "坚定" in current_text and "打招呼" in current_text and len(current_text) < 100:
                    continue # 这是用户发送的提示词，跳过
                    
                if current_text == last_text:
                    stable_count += 1
                    if stable_count >= random.randint(2, 3):
                        return current_text.strip()
                else:
                    stable_count = 0
                    last_text = current_text
                    
            print("⏰ 等待回复超时...")
            return last_text
            
        except Exception as e:
            print(f"⚠️ 发生异常: {e}，等待 5 秒后重试...")
            await asyncio.sleep(5)
            
    return "【系统提示：由于页面异常，本次发言失败】"

async def main():
    async with async_playwright() as p:
        print("🔗 正在连接浏览器 A (9222)...")
        browser_a = await p.chromium.connect_over_cdp("http://localhost:9222")
        # 强制为 A 也新建一个标签页，保证环境干净
        context_a = browser_a.contexts[0]
        page_a = await context_a.new_page()
        await page_a.goto("https://chat.deepseek.com")
        
        print("🔗 正在连接浏览器 B (9223)...")
        browser_b = await p.chromium.connect_over_cdp("http://localhost:9223")
        context_b = browser_b.contexts[0]
        page_b = await context_b.new_page()
        await page_b.goto("https://chat.deepseek.com")
        print(f"✅ 两个浏览器均已就绪！")
        
        await asyncio.sleep(2)
        
        rounds = 2
        prompt_a = "你现在扮演一个坚定的唯物主义者。请用一句话向对方打个招呼，并抛出一个关于宇宙本质的深刻问题。"
        
        print("\n--- 🟢 对话开始 ---")
        print(f"👨‍💻 [A 发起]: {prompt_a}")
        reply_a = await ask_deepseek(page_a, prompt_a)
        print(f"🤖 [A 回复]:\n{reply_a}\n")
        
        current_reply = reply_a
        
        for i in range(1, rounds + 1):
            wait_time = random.uniform(3, 6)
            print(f"\n💤 模拟人类思考，休息 {wait_time:.1f} 秒...")
            await asyncio.sleep(wait_time)
            
            prompt_b = f"对方说：“{current_reply}”。\n请你作为一个坚定的唯心主义者，针对对方的观点进行反驳或回应。要求简短有力，直接给出回答。"
            print(f"👉 [传给 B 的提示]: {prompt_b}")
            reply_b = await ask_deepseek(page_b, prompt_b)
            print(f"🤖 [B 回复]:\n{reply_b}\n")
            
            wait_time_2 = random.uniform(3, 6)
            print(f"💤 模拟人类思考，休息 {wait_time_2:.1f} 秒...")
            await asyncio.sleep(wait_time_2)
            
            prompt_a_next = f"对方反驳说：“{reply_b}”。\n请继续坚持你的唯物主义观点，反驳对方。要求简短有力，直接给出回答。"
            print(f"👉 [传给 A 的提示]: {prompt_a_next}")
            reply_a_next = await ask_deepseek(page_a, prompt_a_next)
            print(f"🤖 [A 回复]:\n{reply_a_next}\n")
            
            current_reply = reply_a_next
            
        print("--- 🏁 对话结束 ---")

if __name__ == "__main__":
    asyncio.run(main())