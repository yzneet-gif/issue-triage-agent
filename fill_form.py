"""Auto-fill the form on 100t.xiaomimimo.com"""
import asyncio
from playwright.async_api import async_playwright

TEXT = """我构建了一个基于 LLM 的 GitHub Issue 智能分诊 Agent，解决开源项目和中大型团队中 Issue 堆积、人工分诊耗时高的核心痛点。以日均 30+ Issue 的项目为例，人工分诊每个 Issue 需 3-5 分钟且依赖资深开发者判断，存在响应延迟和分配不均问题。

核心逻辑流采用多 Agent 协作架构：通过 GitHub Webhook 监听新 Issue 事件触发工作流，启动三个并行子 Agent——①分类 Agent：基于仓库标签体系和 Issue 内容，判断类型（bug/feature/question 等）、优先级和所属模块；②相似度 Agent：检索历史 Issue 列表，通过语义匹配找到关联 Issue 及解决方案；③分配 Agent：根据分类结果和贡献者活跃度推荐处理人。三个子 Agent 的结果汇总到主 Orchestrator，综合推理生成分诊报告，自动执行打标签、添加分诊评论、分配 Assignee 等操作。整个流程平均耗时 30 秒，将人工分诊时间从 3-5 分钟降至仅需确认（约 30 秒），效率提升约 90%。"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        print("1. Opening homepage...")
        await page.goto("https://100t.xiaomimimo.com/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Click "立即申请" button
        print("2. Clicking '立即申请'...")
        apply_btn = page.get_by_text("立即申请")
        if await apply_btn.count() > 0:
            await apply_btn.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="step2_form.png", full_page=True)
            print("   Screenshot: step2_form.png")
        else:
            print("   '立即申请' button not found, checking page...")
            await page.screenshot(path="step2_debug.png", full_page=True)
        
        # Now look for the textarea/input on the form page
        print("3. Looking for input field...")
        
        # Try various selectors
        found = False
        for selector in ["textarea", "[contenteditable='true']", "input[type=text]", 
                         "[role=textbox]", ".ql-editor", "[data-placeholder]", "div[contenteditable]"]:
            els = page.locator(selector)
            count = await els.count()
            if count > 0:
                for i in range(count):
                    el = els.nth(i)
                    try:
                        if await el.is_visible(timeout=1000):
                            box = await el.bounding_box()
                            if box and box["height"] > 50:  # likely the big input area
                                print(f"   Found large input ({selector}, height={box['height']:.0f})")
                                await el.click()
                                await page.wait_for_timeout(500)
                                await el.fill(TEXT)
                                found = True
                                break
                    except:
                        continue
            if found:
                break
        
        if not found:
            # Maybe the question needs to be expanded first
            print("   Trying to find the specific question section...")
            q4 = page.get_by_text("请描述你使用 Agent")
            if await q4.count() > 0:
                print("   Found question 04, clicking...")
                await q4.first.click()
                await page.wait_for_timeout(1000)
                
                # Try again
                for selector in ["textarea", "[contenteditable='true']", "div[contenteditable]"]:
                    els = page.locator(selector)
                    count = await els.count()
                    for i in range(count):
                        el = els.nth(i)
                        try:
                            if await el.is_visible(timeout=1000):
                                await el.click()
                                await page.wait_for_timeout(300)
                                await el.fill(TEXT)
                                found = True
                                break
                        except:
                            continue
                    if found:
                        break
        
        if found:
            await page.wait_for_timeout(1000)
            await page.screenshot(path="step3_filled.png", full_page=True)
            print("4. Text filled! Screenshot: step3_filled.png")
        else:
            await page.screenshot(path="step3_debug.png", full_page=True)
            print("4. Could not find input field. Debug screenshot: step3_debug.png")
            # Print all visible elements for debugging
            all_els = await page.query_selector_all("*")
            for el in all_els[:100]:
                tag = await el.evaluate("e => e.tagName")
                cls = await el.evaluate("e => e.className")
                vis = await el.is_visible()
                if vis and cls:
                    print(f"   <{tag} class='{cls[:60]}'>")
        
        print("\nBrowser staying open for 120 seconds...")
        await page.wait_for_timeout(120000)
        await browser.close()


asyncio.run(main())
