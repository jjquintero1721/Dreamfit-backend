import os
import logging
import requests
import json
from fastapi import HTTPException, status
from typing import Dict, List, Any

service_logger = logging.getLogger("dreamfit_api.content_service")


class ContentService:
    cms_url = ""
    cms_api_key = os.getenv("CMS_API_KEY")

    if os.getenv("ENVIRONMENT") == "prod":
        cms_url = f"https://{os.getenv('CMS_URL')}/api"
    else:
        cms_url = f"https://{os.getenv('CMS_URL')}/api"

    @classmethod
    async def get_workouts(cls):
        service_logger.info("FETCHING_WORKOUTS_FROM_CMS")

        try:
            headers = {"Authorization": f"Bearer {cls.cms_api_key}"}

            service_logger.debug(f"CMS_REQUEST | URL: {cls.cms_url}/muscular-groups")

            response = requests.get(
                f"{cls.cms_url}/muscular-groups?fields=name&populate[workouts][fields]=name,videoUrl",
                headers=headers,
                timeout=5
            )

            if response.ok:
                data = response.json()["data"]
                service_logger.info(f"CMS_REQUEST_SUCCESS | WorkoutGroups: {len(data)}")
                return data
            else:
                service_logger.error(
                    f"CMS_REQUEST_FAILED | Status: {response.status_code} | "
                    f"Response: {response.text[:200]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to retrieve workouts"
                )

        except requests.RequestException as e:
            service_logger.error(f"CMS_REQUEST_EXCEPTION | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Content service unavailable"
            )
        except Exception as e:
            service_logger.error(f"CMS_UNEXPECTED_ERROR | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving workouts"
            )

    @classmethod
    async def get_training_options(cls) -> Dict[str, List[str]]:
        service_logger.info("FETCHING_TRAINING_OPTIONS_FROM_CMS")

        try:
            headers = {"Authorization": f"Bearer {cls.cms_api_key}"}

            training_options = {
                "elements": [],
                "technics": [],
                "rirs": []
            }

            service_logger.debug(f"CMS_REQUEST | URL: {cls.cms_url}/elements")
            elements_response = requests.get(
                f"{cls.cms_url}/elements?fields=name&pagination[limit]=100",
                headers=headers,
                timeout=5
            )

            if elements_response.ok:
                elements_data = elements_response.json()["data"]
                training_options["elements"] = [item["name"] for item in elements_data if item.get("name")]
                service_logger.info(f"ELEMENTS_FETCHED | Count: {len(training_options['elements'])}")
            else:
                service_logger.error(
                    f"ELEMENTS_REQUEST_FAILED | Status: {elements_response.status_code} | "
                    f"Response: {elements_response.text[:200]}"
                )

            service_logger.debug(f"CMS_REQUEST | URL: {cls.cms_url}/technics")
            technics_response = requests.get(
                f"{cls.cms_url}/technics?fields=name&pagination[limit]=100",
                headers=headers,
                timeout=5
            )

            if technics_response.ok:
                technics_data = technics_response.json()["data"]
                training_options["technics"] = [item["name"] for item in technics_data if item.get("name")]
                service_logger.info(f"TECHNICS_FETCHED | Count: {len(training_options['technics'])}")
            else:
                service_logger.error(
                    f"TECHNICS_REQUEST_FAILED | Status: {technics_response.status_code} | "
                    f"Response: {technics_response.text[:200]}"
                )

            service_logger.debug(f"CMS_REQUEST | URL: {cls.cms_url}/rirs")
            rirs_response = requests.get(
                f"{cls.cms_url}/rirs?fields=name&pagination[limit]=100",
                headers=headers,
                timeout=5
            )

            if rirs_response.ok:
                rirs_data = rirs_response.json()["data"]
                training_options["rirs"] = [item["name"] for item in rirs_data if item.get("name")]
                service_logger.info(f"RIRS_FETCHED | Count: {len(training_options['rirs'])}")
            else:
                service_logger.error(
                    f"RIRS_REQUEST_FAILED | Status: {rirs_response.status_code} | "
                    f"Response: {rirs_response.text[:200]}"
                )

            if not any([training_options["elements"], training_options["technics"], training_options["rirs"]]):
                service_logger.warning("NO_TRAINING_OPTIONS_RETRIEVED")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No training options found in CMS"
                )

            service_logger.info(
                f"TRAINING_OPTIONS_SUCCESS | Elements: {len(training_options['elements'])} | "
                f"Technics: {len(training_options['technics'])} | RIRs: {len(training_options['rirs'])}"
            )

            return training_options

        except requests.RequestException as e:
            service_logger.error(f"CMS_REQUEST_EXCEPTION | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Content service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            service_logger.error(f"CMS_UNEXPECTED_ERROR | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving training options"
            )

    import json

    @classmethod
    async def get_plans(cls):
        service_logger.info("FETCHING_PLANS_FROM_CMS")

        try:
            headers = {"Authorization": f"Bearer {cls.cms_api_key}"} if cls.cms_api_key else {}

            url = (
                f"{cls.cms_url}/plans"
                "?populate[graphics][fields]=name,slug"
                "&fields=name,slug,monthlyPrice,anualPrice,maxDailyMealPlans,maxMentees,contactButton"
                "&pagination[limit]=100"
            )
            service_logger.debug(f"CMS_REQUEST | URL: {url} | Auth present: {bool(cls.cms_api_key)}")

            response = requests.get(url, headers=headers, timeout=10)
            service_logger.debug(f"CMS_RESPONSE_STATUS: {response.status_code}")

            try:
                raw = response.json()
                snippet = json.dumps(raw, ensure_ascii=False)[:3000]
                service_logger.debug(f"CMS_RAW_RESPONSE_SNIPPET: {snippet}")
            except Exception as e:
                service_logger.error(f"CMS_JSON_PARSE_ERROR: {str(e)} | text_snippet: {response.text[:1000]}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from CMS"
                )

            if not response.ok:
                service_logger.error(
                    f"CMS_REQUEST_FAILED | Status: {response.status_code} | Response: {response.text[:200]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to retrieve plans"
                )

            data = raw.get("data") if isinstance(raw, dict) else raw
            if data is None:
                data = []

            if isinstance(data, dict) and "plans" in data:
                data = data["plans"]

            service_logger.info(
                f"CMS_REQUEST_SUCCESS | Raw plans items: {len(data) if isinstance(data, list) else 'unknown'}")

            formatted_plans = []

            def to_number(v):
                try:
                    return float(v)
                except Exception:
                    return None

            for plan in data:
                attrs = {}
                if isinstance(plan, dict):
                    attrs = plan.get("attributes") or {}
                    if not attrs:
                        attrs = {
                            "name": plan.get("name"),
                            "slug": plan.get("slug"),
                            "monthlyPrice": plan.get("monthlyPrice"),
                            "anualPrice": plan.get("anualPrice"),
                            "maxDailyMealPlans": plan.get("maxDailyMealPlans"),
                            "maxMentees": plan.get("maxMentees"),
                            "contactButton": plan.get("contactButton"),
                            "graphics": plan.get("graphics"),
                        }
                else:
                    attrs = {}

                graphics_list = []
                raw_graphics = attrs.get("graphics") or plan.get("graphics") or {}
                if isinstance(raw_graphics, dict) and "data" in raw_graphics:
                    g_items = raw_graphics.get("data", [])
                elif isinstance(raw_graphics, list):
                    g_items = raw_graphics
                else:
                    g_items = []

                for g in g_items:
                    if not isinstance(g, dict):
                        continue
                    g_attrs = g.get("attributes") or g
                    graphics_list.append({
                        "id": g.get("id") or g_attrs.get("id"),
                        "name": g_attrs.get("name"),
                        "slug": g_attrs.get("slug")
                    })

                formatted_plan = {
                    "id": plan.get("id") or attrs.get("id"),
                    "name": attrs.get("name"),
                    "slug": attrs.get("slug"),
                    "monthlyPrice": to_number(attrs.get("monthlyPrice")),
                    "anualPrice": to_number(attrs.get("anualPrice")),
                    "maxDailyMealPlans": attrs.get("maxDailyMealPlans"),
                    "maxMentees": attrs.get("maxMentees"),
                    "contactButton": bool(attrs.get("contactButton")),
                    "graphics": graphics_list
                }

                formatted_plans.append(formatted_plan)

            service_logger.info(f"FORMATTED_PLANS_COUNT: {len(formatted_plans)}")
            return formatted_plans

        except requests.RequestException as e:
            service_logger.error(f"CMS_REQUEST_EXCEPTION | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Content service unavailable"
            )
        except Exception as e:
            service_logger.error(f"CMS_UNEXPECTED_ERROR | Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving plans"
            )