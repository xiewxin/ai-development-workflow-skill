<?php

declare(strict_types=1);

final class OrderService
{
    public function __construct(
        private OrderRepository $orderRepository,
        private PromotionService $promotionService,
    ) {
    }

    /** 建立訂單並回傳結果。 */
    public function create(array $input): array
    {
        return $this->orderRepository->create($input);
    }
}
